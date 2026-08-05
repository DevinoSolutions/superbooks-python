"""The sync and async SuperBooks clients."""

from __future__ import annotations

import os
from types import TracebackType
from typing import Any

import httpx

from ._generated._bind import AsyncNamespaces, SyncNamespaces
from ._transport import (
    DEFAULT_BASE_URL,
    DEFAULT_TIMEOUT,
    AsyncTransport,
    SyncTransport,
)

API_KEY_ENV_VAR = "SUPERBOOKS_API_KEY"
BASE_URL_ENV_VAR = "SUPERBOOKS_BASE_URL"


def _resolve_api_key(api_key: str | None) -> str:
    resolved = api_key or os.environ.get(API_KEY_ENV_VAR)
    if not resolved:
        raise ValueError(
            "No API key provided. Pass api_key=... or set the "
            f"{API_KEY_ENV_VAR} environment variable. Mint a key in "
            "SuperBooks under Settings -> Developer."
        )
    return resolved


def _resolve_base_url(base_url: str | None) -> str:
    return base_url or os.environ.get(BASE_URL_ENV_VAR) or DEFAULT_BASE_URL


class SyncTools:
    """Escape hatch for tools the generated namespaces do not cover."""

    def __init__(self, transport: SyncTransport) -> None:
        self._transport = transport

    def list(self) -> list[dict[str, Any]]:
        """Return every tool the current credential can see, as raw MCP dicts.

        The set is filtered server-side by the key's scopes, so a read-only key
        will not see write or destructive tools here.
        """
        return self._transport.list_tools()

    def call(self, name: str, arguments: dict[str, Any] | None = None) -> Any:
        """Invoke any tool by name, bypassing the generated signatures."""
        return self._transport.call_tool(name, arguments or {})


class AsyncTools:
    """Escape hatch for tools the generated namespaces do not cover."""

    def __init__(self, transport: AsyncTransport) -> None:
        self._transport = transport

    async def list(self) -> list[dict[str, Any]]:
        """Return every tool the current credential can see, as raw MCP dicts."""
        return await self._transport.list_tools()

    async def call(self, name: str, arguments: dict[str, Any] | None = None) -> Any:
        """Invoke any tool by name, bypassing the generated signatures."""
        return await self._transport.call_tool(name, arguments or {})


class SuperBooks(SyncNamespaces):
    """Synchronous SuperBooks client.

    Example::

        from superbooks import SuperBooks

        sb = SuperBooks(api_key="sb_your_api_key_here")
        page = sb.transactions.list(limit=10)

    Args:
        api_key: A SuperBooks API key (``sb_``-prefixed). Falls back to the
            ``SUPERBOOKS_API_KEY`` environment variable.
        base_url: API root. Falls back to ``SUPERBOOKS_BASE_URL``, then to
            ``https://api.superbooks.io``.
        timeout: Per-request timeout in seconds.
        max_retries: How many times to automatically retry a request that was
            rate limited (HTTP 429). Defaults to ``0`` — no retry — because the
            API's ``Retry-After`` is a full 60 seconds and silently blocking a
            caller for minutes is worse than surfacing
            :class:`~superbooks.RateLimitError`. Set it to opt in; each sleep
            is capped at 60 seconds.
        http_client: Bring your own ``httpx.Client`` (proxies, custom
            transports, connection pool tuning). You keep ownership: closing
            this client will not close yours.
    """

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        *,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = 0,
        http_client: httpx.Client | None = None,
    ) -> None:
        self._transport = SyncTransport(
            _resolve_api_key(api_key),
            _resolve_base_url(base_url),
            timeout=timeout,
            max_retries=max_retries,
            http_client=http_client,
        )
        self.tools = SyncTools(self._transport)
        self._bind_namespaces(self._transport)

    def close(self) -> None:
        self._transport.close()

    def __enter__(self) -> SuperBooks:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.close()


class AsyncSuperBooks(AsyncNamespaces):
    """Asynchronous SuperBooks client.

    Mirrors :class:`SuperBooks` exactly; every namespace method is a coroutine.

    Example::

        import asyncio
        from superbooks import AsyncSuperBooks

        async def main() -> None:
            async with AsyncSuperBooks(api_key="sb_your_api_key_here") as sb:
                page = await sb.transactions.list(limit=10)

        asyncio.run(main())

    See :class:`SuperBooks` for the argument reference.
    """

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        *,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = 0,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        self._transport = AsyncTransport(
            _resolve_api_key(api_key),
            _resolve_base_url(base_url),
            timeout=timeout,
            max_retries=max_retries,
            http_client=http_client,
        )
        self.tools = AsyncTools(self._transport)
        self._bind_namespaces(self._transport)

    async def aclose(self) -> None:
        await self._transport.aclose()

    async def __aenter__(self) -> AsyncSuperBooks:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        await self.aclose()
