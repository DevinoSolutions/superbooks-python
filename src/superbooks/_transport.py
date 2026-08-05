"""HTTP transports for the SuperBooks MCP endpoint.

Two classes, one protocol: :class:`SyncTransport` and :class:`AsyncTransport`
are line-for-line parallel and both delegate every parsing and error decision
to :mod:`superbooks._protocol`. Only the I/O differs.
"""

from __future__ import annotations

import asyncio
import itertools
import threading
import time
from types import TracebackType
from typing import Any

import httpx

from . import _protocol as proto
from ._errors import ConnectionError as SuperBooksConnectionError
from ._errors import RateLimitError

DEFAULT_BASE_URL = "https://api.superbooks.io"
DEFAULT_TIMEOUT = 60.0

# Ceiling on how long a single automatic retry will sleep, so a large
# server-sent Retry-After cannot silently park a caller's thread for minutes.
MAX_RETRY_SLEEP_SECONDS = 60.0


def _endpoint(base_url: str) -> str:
    return f"{base_url.rstrip('/')}/mcp"


def _response_headers(response: httpx.Response) -> dict[str, str]:
    return dict(response.headers)


class _TransportBase:
    """State and pure helpers shared by both transports."""

    def __init__(
        self,
        api_key: str,
        base_url: str,
        max_retries: int,
    ) -> None:
        if not api_key:
            raise ValueError(
                "An API key is required. Pass api_key=... or set "
                "SUPERBOOKS_API_KEY in the environment."
            )
        self._api_key = api_key
        self._url = _endpoint(base_url)
        self._max_retries = max(0, max_retries)
        self._ids = itertools.count(1)
        self._session_id: str | None = None
        self._protocol_version: str | None = None
        self._initialized = False

    def _next_id(self) -> int:
        return next(self._ids)

    def _headers(self) -> dict[str, str]:
        return proto.build_headers(
            self._api_key,
            session_id=self._session_id,
            protocol_version=self._protocol_version,
        )

    def _absorb_initialize(self, response: httpx.Response, result: Any) -> None:
        """Record the negotiated session id and protocol version."""
        session_id = response.headers.get("mcp-session-id")
        if session_id:
            self._session_id = session_id
        if isinstance(result, dict):
            negotiated = result.get("protocolVersion")
            if isinstance(negotiated, str) and negotiated:
                self._protocol_version = negotiated
        if self._protocol_version is None:
            self._protocol_version = proto.MCP_PROTOCOL_VERSION
        self._initialized = True

    def _retry_delay(self, exc: RateLimitError, attempt: int) -> float | None:
        """Seconds to sleep before retry, or ``None`` to give up."""
        if attempt >= self._max_retries:
            return None
        delay = exc.retry_after if exc.retry_after is not None else 1.0
        return min(delay, MAX_RETRY_SLEEP_SECONDS)


class SyncTransport(_TransportBase):
    def __init__(
        self,
        api_key: str,
        base_url: str = DEFAULT_BASE_URL,
        *,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = 0,
        http_client: httpx.Client | None = None,
    ) -> None:
        super().__init__(api_key, base_url, max_retries)
        self._owns_client = http_client is None
        self._client = http_client or httpx.Client(timeout=timeout)
        self._lock = threading.Lock()

    def _post(self, payload: dict[str, Any]) -> httpx.Response:
        attempt = 0
        while True:
            try:
                response = self._client.post(
                    self._url, json=payload, headers=self._headers()
                )
            except httpx.HTTPError as exc:
                raise SuperBooksConnectionError(
                    f"Could not reach the SuperBooks API at {self._url}: {exc}"
                ) from exc
            try:
                proto.raise_for_status(
                    response.status_code, _response_headers(response), response.text
                )
            except RateLimitError as exc:
                delay = self._retry_delay(exc, attempt)
                if delay is None:
                    raise
                time.sleep(delay)
                attempt += 1
                continue
            return response

    def _send(self, payload: dict[str, Any]) -> tuple[httpx.Response, Any]:
        response = self._post(payload)
        messages = proto.decode_body(
            response.headers.get("content-type"), response.text
        )
        return response, proto.extract_result(messages, payload["id"])

    def _notify(self, payload: dict[str, Any]) -> None:
        self._post(payload)

    def _ensure_initialized(self) -> None:
        if self._initialized:
            return
        with self._lock:
            if self._initialized:
                return
            payload = proto.initialize_payload(self._next_id())
            response, result = self._send(payload)
            self._absorb_initialize(response, result)
            self._notify(proto.initialized_notification())

    def request(self, method: str, params: dict[str, Any] | None = None) -> Any:
        self._ensure_initialized()
        _, result = self._send(proto.request_payload(self._next_id(), method, params))
        return result

    def list_tools(self) -> list[dict[str, Any]]:
        result = self.request("tools/list")
        tools = result.get("tools") if isinstance(result, dict) else None
        return tools if isinstance(tools, list) else []

    def call_tool(self, name: str, arguments: dict[str, Any] | None = None) -> Any:
        result = self.request(
            "tools/call", {"name": name, "arguments": arguments or {}}
        )
        return proto.unwrap_tool_result(result)

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    def __enter__(self) -> SyncTransport:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.close()


class AsyncTransport(_TransportBase):
    def __init__(
        self,
        api_key: str,
        base_url: str = DEFAULT_BASE_URL,
        *,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = 0,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        super().__init__(api_key, base_url, max_retries)
        self._owns_client = http_client is None
        self._client = http_client or httpx.AsyncClient(timeout=timeout)
        self._lock = asyncio.Lock()

    async def _post(self, payload: dict[str, Any]) -> httpx.Response:
        attempt = 0
        while True:
            try:
                response = await self._client.post(
                    self._url, json=payload, headers=self._headers()
                )
            except httpx.HTTPError as exc:
                raise SuperBooksConnectionError(
                    f"Could not reach the SuperBooks API at {self._url}: {exc}"
                ) from exc
            try:
                proto.raise_for_status(
                    response.status_code, _response_headers(response), response.text
                )
            except RateLimitError as exc:
                delay = self._retry_delay(exc, attempt)
                if delay is None:
                    raise
                await asyncio.sleep(delay)
                attempt += 1
                continue
            return response

    async def _send(self, payload: dict[str, Any]) -> tuple[httpx.Response, Any]:
        response = await self._post(payload)
        messages = proto.decode_body(
            response.headers.get("content-type"), response.text
        )
        return response, proto.extract_result(messages, payload["id"])

    async def _notify(self, payload: dict[str, Any]) -> None:
        await self._post(payload)

    async def _ensure_initialized(self) -> None:
        if self._initialized:
            return
        async with self._lock:
            if self._initialized:
                return
            payload = proto.initialize_payload(self._next_id())
            response, result = await self._send(payload)
            self._absorb_initialize(response, result)
            await self._notify(proto.initialized_notification())

    async def request(self, method: str, params: dict[str, Any] | None = None) -> Any:
        await self._ensure_initialized()
        _, result = await self._send(
            proto.request_payload(self._next_id(), method, params)
        )
        return result

    async def list_tools(self) -> list[dict[str, Any]]:
        result = await self.request("tools/list")
        tools = result.get("tools") if isinstance(result, dict) else None
        return tools if isinstance(tools, list) else []

    async def call_tool(
        self, name: str, arguments: dict[str, Any] | None = None
    ) -> Any:
        result = await self.request(
            "tools/call", {"name": name, "arguments": arguments or {}}
        )
        return proto.unwrap_tool_result(result)

    async def aclose(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    async def __aenter__(self) -> AsyncTransport:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        await self.aclose()
