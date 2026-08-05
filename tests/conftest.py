"""Shared fixtures: an in-process fake MCP server built on httpx.MockTransport.

No test in this suite touches the network, and no real credential appears
anywhere — ``sb_your_api_key_here`` is an obvious placeholder.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

import httpx
import pytest

TEST_API_KEY = "sb_your_api_key_here"
TEST_SESSION_ID = "mcp-session-for-tests"


@dataclass
class RecordedRequest:
    method: str | None
    body: dict[str, Any]
    headers: httpx.Headers
    url: str


@dataclass
class FakeMCP:
    """A minimal MCP streamable-HTTP server good enough to drive the client.

    Args:
        results: tool name -> structured payload returned by ``tools/call``.
        tools: what ``tools/list`` reports.
        sse: answer with ``text/event-stream`` instead of JSON.
        status: force this HTTP status on every request (for error tests).
        response_headers: extra headers on forced-status responses.
        fail_times: return ``status`` this many times, then succeed.
    """

    results: dict[str, Any] = field(default_factory=dict)
    tools: list[dict[str, Any]] = field(default_factory=list)
    sse: bool = False
    status: int | None = None
    response_headers: dict[str, str] = field(default_factory=dict)
    fail_times: int | None = None
    requests: list[RecordedRequest] = field(default_factory=list)
    tool_is_error: bool = False
    jsonrpc_error: dict[str, Any] | None = None

    def __call__(self, request: httpx.Request) -> httpx.Response:
        raw = request.content.decode() if request.content else ""
        body = json.loads(raw) if raw.strip() else {}
        self.requests.append(
            RecordedRequest(
                method=body.get("method"),
                body=body,
                headers=request.headers,
                url=str(request.url),
            )
        )

        if self.status is not None and (
            self.fail_times is None or self.failures_sent < self.fail_times
        ):
            self.failures_sent += 1
            return httpx.Response(
                self.status, headers=self.response_headers, text="upstream said no"
            )

        method = body.get("method")
        if method == "initialize":
            return self._respond(
                body["id"],
                {
                    "protocolVersion": "2025-06-18",
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": "superbooks", "version": "1.0.0"},
                },
                headers={"mcp-session-id": TEST_SESSION_ID},
            )

        if body.get("id") is None:
            # Notification: acknowledged, no body.
            return httpx.Response(202)

        if self.jsonrpc_error is not None:
            return self._raw(
                {"jsonrpc": "2.0", "id": body["id"], "error": self.jsonrpc_error}
            )

        if method == "tools/list":
            return self._respond(body["id"], {"tools": self.tools})

        if method == "tools/call":
            name = body["params"]["name"]
            payload = self.results.get(name, {"ok": True, "tool": name})
            result: dict[str, Any] = {
                "content": [{"type": "text", "text": json.dumps(payload)}]
            }
            if self.tool_is_error:
                result["isError"] = True
            else:
                result["structuredContent"] = payload
            return self._respond(body["id"], result)

        return self._respond(body["id"], {})

    failures_sent: int = 0

    def _respond(
        self,
        request_id: Any,
        result: dict[str, Any],
        headers: dict[str, str] | None = None,
    ) -> httpx.Response:
        return self._raw(
            {"jsonrpc": "2.0", "id": request_id, "result": result}, headers
        )

    def _raw(
        self, message: dict[str, Any], headers: dict[str, str] | None = None
    ) -> httpx.Response:
        payload = json.dumps(message)
        if self.sse:
            return httpx.Response(
                200,
                headers={"content-type": "text/event-stream", **(headers or {})},
                text=f"event: message\ndata: {payload}\n\n",
            )
        return httpx.Response(
            200,
            headers={"content-type": "application/json", **(headers or {})},
            text=payload,
        )

    # Convenience accessors for assertions.
    def calls_to(self, method: str) -> list[RecordedRequest]:
        return [r for r in self.requests if r.method == method]

    def tool_call_arguments(self, name: str) -> dict[str, Any]:
        for record in self.calls_to("tools/call"):
            if record.body["params"]["name"] == name:
                return record.body["params"]["arguments"]
        raise AssertionError(f"no tools/call recorded for {name}")


def sync_client(fake: FakeMCP, **kwargs: Any):
    from superbooks import SuperBooks

    return SuperBooks(
        api_key=TEST_API_KEY,
        http_client=httpx.Client(transport=httpx.MockTransport(fake)),
        **kwargs,
    )


def async_client(fake: FakeMCP, **kwargs: Any):
    from superbooks import AsyncSuperBooks

    return AsyncSuperBooks(
        api_key=TEST_API_KEY,
        http_client=httpx.AsyncClient(transport=httpx.MockTransport(fake)),
        **kwargs,
    )


@pytest.fixture
def fake() -> FakeMCP:
    return FakeMCP()


@pytest.fixture
def sb(fake: FakeMCP):
    client = sync_client(fake)
    yield client
    client.close()
