"""I/O-free MCP protocol logic.

Everything here is a pure function over bytes and dicts: payload construction,
Server-Sent Events parsing, HTTP status mapping, and JSON-RPC result
extraction. The sync and async transports differ only in how they perform the
HTTP round trip, so all the parts that could disagree between them live here
and are exercised once by the tests.
"""

from __future__ import annotations

import json
from typing import Any

from ._errors import (
    APIError,
    AuthenticationError,
    AuthorizationError,
    ProtocolError,
    RateLimitError,
    ToolError,
)
from ._version import __version__

# Protocol revision this client is written against. The server echoes the
# version it agreed to during `initialize`; we send that one back on later
# requests rather than assuming ours won.
MCP_PROTOCOL_VERSION = "2025-06-18"

CLIENT_NAME = "superbooks-python"

# Bodies are only ever surfaced inside exception messages, so keep them short.
_MAX_BODY_CHARS = 2048


def build_headers(
    api_key: str,
    *,
    session_id: str | None = None,
    protocol_version: str | None = None,
) -> dict[str, str]:
    """Build request headers for a call to the MCP endpoint.

    The API key travels as ``Authorization: Bearer <key>``; SuperBooks keys are
    ``sb_``-prefixed and the server routes on that prefix.
    """
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        # Streamable HTTP servers may answer with either a plain JSON body or
        # an SSE stream; we parse both, so advertise both.
        "Accept": "application/json, text/event-stream",
        "User-Agent": f"{CLIENT_NAME}/{__version__}",
    }
    if session_id:
        headers["Mcp-Session-Id"] = session_id
    if protocol_version:
        headers["MCP-Protocol-Version"] = protocol_version
    return headers


def initialize_payload(request_id: int) -> dict[str, Any]:
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "method": "initialize",
        "params": {
            "protocolVersion": MCP_PROTOCOL_VERSION,
            "capabilities": {},
            "clientInfo": {"name": CLIENT_NAME, "version": __version__},
        },
    }


def initialized_notification() -> dict[str, Any]:
    """The post-handshake notification the MCP spec requires clients to send."""
    return {"jsonrpc": "2.0", "method": "notifications/initialized"}


def request_payload(
    request_id: int, method: str, params: dict[str, Any] | None = None
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "jsonrpc": "2.0",
        "id": request_id,
        "method": method,
    }
    if params is not None:
        payload["params"] = params
    return payload


def parse_retry_after(value: str | None) -> float | None:
    """Parse a ``Retry-After`` header expressed in seconds.

    HTTP-date form is accepted by the spec but the SuperBooks API always sends
    a delta in seconds; anything unparseable yields ``None`` rather than a
    misleading number.
    """
    if not value:
        return None
    try:
        seconds = float(value.strip())
    except ValueError:
        return None
    return seconds if seconds >= 0 else None


def _truncate(body: str) -> str:
    if len(body) <= _MAX_BODY_CHARS:
        return body
    return f"{body[:_MAX_BODY_CHARS]}… (truncated)"


def raise_for_status(status_code: int, headers: dict[str, str], body: str) -> None:
    """Map an unsuccessful HTTP response onto the SDK error hierarchy.

    Returns silently for 2xx.
    """
    if 200 <= status_code < 300:
        return

    snippet = _truncate(body)
    lowered = {k.lower(): v for k, v in headers.items()}

    if status_code == 401:
        raise AuthenticationError(
            "Authentication failed (401). Check that SUPERBOOKS_API_KEY is a "
            "current, unrevoked SuperBooks API key.",
            status_code=status_code,
            body=snippet,
        )
    if status_code == 403:
        raise AuthorizationError(
            "Not permitted (403). The credential is valid but lacks the scope "
            "for this tool, or has no active team.",
            status_code=status_code,
            body=snippet,
        )
    if status_code == 429:
        retry_after = parse_retry_after(lowered.get("retry-after"))
        suffix = f" Retry after {retry_after:g}s." if retry_after else ""
        raise RateLimitError(
            f"Rate limit exceeded (429).{suffix}",
            status_code=status_code,
            body=snippet,
            retry_after=retry_after,
        )
    raise APIError(
        f"SuperBooks API request failed with status {status_code}.",
        status_code=status_code,
        body=snippet,
    )


def parse_sse(text: str) -> list[dict[str, Any]]:
    """Extract JSON payloads from a Server-Sent Events stream.

    Events are separated by a blank line; ``data:`` lines within one event are
    joined with newlines per the SSE spec. Non-JSON payloads (comments,
    keep-alives) are skipped rather than raising, so a heartbeat cannot break a
    call.
    """
    messages: list[dict[str, Any]] = []
    data_lines: list[str] = []

    def flush() -> None:
        if not data_lines:
            return
        raw = "\n".join(data_lines)
        data_lines.clear()
        if not raw.strip():
            return
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            return
        if isinstance(parsed, dict):
            messages.append(parsed)

    for line in text.splitlines():
        if not line.strip():
            flush()
            continue
        if line.startswith(":"):
            continue
        if line.startswith("data:"):
            data_lines.append(line[5:].lstrip(" "))
    flush()
    return messages


def decode_body(content_type: str | None, body: str) -> list[dict[str, Any]]:
    """Decode a response body into a list of JSON-RPC messages.

    Handles both transports of MCP streamable HTTP: a single JSON object (or
    batch array) and an SSE stream.
    """
    if not body.strip():
        return []

    if content_type and "text/event-stream" in content_type.lower():
        return parse_sse(body)

    try:
        parsed = json.loads(body)
    except json.JSONDecodeError:
        # Some proxies label an SSE stream as JSON; fall back before failing.
        recovered = parse_sse(body)
        if recovered:
            return recovered
        raise ProtocolError(
            f"Expected a JSON-RPC response but got: {_truncate(body)}"
        ) from None

    if isinstance(parsed, list):
        return [m for m in parsed if isinstance(m, dict)]
    if isinstance(parsed, dict):
        return [parsed]
    raise ProtocolError(
        f"Expected a JSON-RPC object or batch but got: {_truncate(body)}"
    )


def extract_result(messages: list[dict[str, Any]], request_id: int) -> Any:
    """Pull the result for ``request_id`` out of decoded JSON-RPC messages.

    Raises :class:`ToolError` if the server answered with a JSON-RPC error.
    """
    for message in messages:
        if message.get("id") != request_id:
            continue
        if "error" in message:
            error = message["error"] or {}
            raise ToolError(
                str(error.get("message") or "The SuperBooks API returned an error."),
                code=error.get("code"),
                data=error.get("data"),
            )
        if "result" in message:
            return message["result"]

    raise ProtocolError(
        f"No JSON-RPC response for request id {request_id} in the server reply."
    )


def unwrap_tool_result(result: Any) -> Any:
    """Reduce an MCP ``tools/call`` result to the useful payload.

    Prefers ``structuredContent`` when the tool provides it; otherwise returns
    the raw ``content`` blocks. A result flagged ``isError`` is raised as a
    :class:`ToolError` carrying the text the tool produced.
    """
    if not isinstance(result, dict):
        return result

    content = result.get("content")

    if result.get("isError"):
        raise ToolError(_content_to_text(content) or "The tool reported an error.")

    if result.get("structuredContent") is not None:
        return result["structuredContent"]
    if content is not None:
        return content
    return result


def _content_to_text(content: Any) -> str:
    if not isinstance(content, list):
        return ""
    parts = [
        block["text"]
        for block in content
        if isinstance(block, dict) and isinstance(block.get("text"), str)
    ]
    return "\n".join(parts)


def prune_arguments(arguments: dict[str, Any]) -> dict[str, Any]:
    """Drop unset (``None``) arguments.

    Omitting a parameter lets the server apply its own default, which is not
    the same as sending an explicit null — so ``None`` means "don't send".
    """
    return {k: v for k, v in arguments.items() if v is not None}
