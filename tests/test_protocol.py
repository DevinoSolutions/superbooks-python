"""Unit tests for the I/O-free protocol layer."""

from __future__ import annotations

import pytest

from superbooks import ProtocolError, ToolError
from superbooks._protocol import (
    build_headers,
    decode_body,
    extract_result,
    parse_sse,
    prune_arguments,
    unwrap_tool_result,
)


def test_headers_carry_the_bearer_token() -> None:
    headers = build_headers("sb_your_api_key_here")
    assert headers["Authorization"] == "Bearer sb_your_api_key_here"
    assert headers["Content-Type"] == "application/json"
    assert "superbooks-python/" in headers["User-Agent"]


def test_session_and_protocol_headers_are_optional() -> None:
    assert "Mcp-Session-Id" not in build_headers("sb_your_api_key_here")
    with_session = build_headers(
        "sb_your_api_key_here", session_id="abc", protocol_version="2025-06-18"
    )
    assert with_session["Mcp-Session-Id"] == "abc"
    assert with_session["MCP-Protocol-Version"] == "2025-06-18"


def test_parse_sse_reads_a_single_event() -> None:
    stream = 'event: message\ndata: {"jsonrpc":"2.0","id":1,"result":{"ok":true}}\n\n'
    assert parse_sse(stream) == [{"jsonrpc": "2.0", "id": 1, "result": {"ok": True}}]


def test_parse_sse_joins_multiline_data() -> None:
    stream = 'data: {"jsonrpc":"2.0",\ndata: "id":1,\ndata: "result":{}}\n\n'
    assert parse_sse(stream) == [{"jsonrpc": "2.0", "id": 1, "result": {}}]


def test_parse_sse_skips_comments_and_keepalives() -> None:
    stream = ': keep-alive\n\ndata: {"id":1}\n\n: another\n\n'
    assert parse_sse(stream) == [{"id": 1}]


def test_parse_sse_reads_several_events() -> None:
    stream = 'data: {"id":1}\n\ndata: {"id":2}\n\n'
    assert [m["id"] for m in parse_sse(stream)] == [1, 2]


def test_decode_body_handles_json_and_sse() -> None:
    assert decode_body("application/json", '{"id":1}') == [{"id": 1}]
    assert decode_body("text/event-stream; charset=utf-8", 'data: {"id":1}\n\n') == [
        {"id": 1}
    ]


def test_decode_body_handles_a_batch() -> None:
    assert decode_body("application/json", '[{"id":1},{"id":2}]') == [
        {"id": 1},
        {"id": 2},
    ]


def test_decode_body_recovers_mislabelled_sse() -> None:
    # A proxy that stamps application/json on an SSE stream should not break us.
    assert decode_body("application/json", 'data: {"id":1}\n\n') == [{"id": 1}]


def test_decode_body_rejects_garbage() -> None:
    with pytest.raises(ProtocolError):
        decode_body("application/json", "not json at all")


def test_decode_body_of_empty_response() -> None:
    assert decode_body("application/json", "") == []


def test_extract_result_matches_on_request_id() -> None:
    messages = [{"id": 1, "result": "a"}, {"id": 2, "result": "b"}]
    assert extract_result(messages, 2) == "b"


def test_extract_result_raises_when_the_id_is_absent() -> None:
    with pytest.raises(ProtocolError, match="request id 9"):
        extract_result([{"id": 1, "result": "a"}], 9)


def test_extract_result_surfaces_jsonrpc_errors() -> None:
    messages = [{"id": 1, "error": {"code": -32601, "message": "No such method"}}]
    with pytest.raises(ToolError) as info:
        extract_result(messages, 1)
    assert info.value.code == -32601


def test_unwrap_prefers_structured_content() -> None:
    result = {
        "content": [{"type": "text", "text": "{}"}],
        "structuredContent": {"items": []},
    }
    assert unwrap_tool_result(result) == {"items": []}


def test_unwrap_falls_back_to_content_blocks() -> None:
    blocks = [{"type": "text", "text": "hello"}]
    assert unwrap_tool_result({"content": blocks}) == blocks


def test_unwrap_raises_on_is_error_with_the_tool_text() -> None:
    result = {
        "content": [{"type": "text", "text": "customer not found"}],
        "isError": True,
    }
    with pytest.raises(ToolError, match="customer not found"):
        unwrap_tool_result(result)


def test_unwrap_is_error_wins_over_structured_content() -> None:
    result = {
        "content": [{"type": "text", "text": "boom"}],
        "structuredContent": {"partial": True},
        "isError": True,
    }
    with pytest.raises(ToolError, match="boom"):
        unwrap_tool_result(result)


def test_prune_drops_none_but_keeps_falsy_values() -> None:
    assert prune_arguments(
        {"a": None, "b": 0, "c": False, "d": "", "e": [], "f": "x"}
    ) == {"b": 0, "c": False, "d": "", "e": [], "f": "x"}
