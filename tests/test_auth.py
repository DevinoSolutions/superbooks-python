"""Credential handling and the MCP handshake."""

from __future__ import annotations

import httpx
import pytest

from superbooks import SuperBooks
from superbooks._transport import SyncTransport

from .conftest import TEST_API_KEY, TEST_SESSION_ID, FakeMCP, sync_client


def test_api_key_is_sent_as_bearer(fake: FakeMCP, sb: SuperBooks) -> None:
    sb.team.get()
    for record in fake.requests:
        assert record.headers["authorization"] == f"Bearer {TEST_API_KEY}"


def test_accept_header_allows_json_and_sse(fake: FakeMCP, sb: SuperBooks) -> None:
    sb.team.get()
    accept = fake.requests[0].headers["accept"]
    assert "application/json" in accept
    assert "text/event-stream" in accept


def test_handshake_runs_once_then_reuses_the_session(
    fake: FakeMCP, sb: SuperBooks
) -> None:
    sb.team.get()
    sb.team.get()

    assert len(fake.calls_to("initialize")) == 1
    assert len(fake.calls_to("notifications/initialized")) == 1

    # Every request after the handshake carries the server's session id and the
    # negotiated protocol version.
    post_handshake = fake.calls_to("tools/call")
    assert post_handshake
    for record in post_handshake:
        assert record.headers["mcp-session-id"] == TEST_SESSION_ID
        assert record.headers["mcp-protocol-version"] == "2025-06-18"


def test_initialize_is_sent_before_any_tool_call(fake: FakeMCP, sb: SuperBooks) -> None:
    sb.team.get()
    assert [r.method for r in fake.requests][:3] == [
        "initialize",
        "notifications/initialized",
        "tools/call",
    ]


def test_requests_go_to_the_mcp_endpoint(fake: FakeMCP, sb: SuperBooks) -> None:
    sb.team.get()
    assert fake.requests[0].url == "https://api.superbooks.io/mcp"


def test_base_url_override_and_trailing_slash(fake: FakeMCP) -> None:
    client = SuperBooks(
        api_key=TEST_API_KEY,
        base_url="https://staging.example.com/",
        http_client=httpx.Client(transport=httpx.MockTransport(fake)),
    )
    client.team.get()
    assert fake.requests[0].url == "https://staging.example.com/mcp"
    client.close()


def test_api_key_read_from_environment(
    fake: FakeMCP, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("SUPERBOOKS_API_KEY", "sb_test_from_env")
    client = SuperBooks(http_client=httpx.Client(transport=httpx.MockTransport(fake)))
    client.team.get()
    assert fake.requests[0].headers["authorization"] == "Bearer sb_test_from_env"
    client.close()


def test_base_url_read_from_environment(
    fake: FakeMCP, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("SUPERBOOKS_BASE_URL", "https://eu.example.com")
    client = SuperBooks(
        api_key=TEST_API_KEY,
        http_client=httpx.Client(transport=httpx.MockTransport(fake)),
    )
    client.team.get()
    assert fake.requests[0].url == "https://eu.example.com/mcp"
    client.close()


def test_missing_api_key_fails_fast(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SUPERBOOKS_API_KEY", raising=False)
    with pytest.raises(ValueError, match="SUPERBOOKS_API_KEY"):
        SuperBooks()


def test_explicit_key_beats_the_environment(
    fake: FakeMCP, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("SUPERBOOKS_API_KEY", "sb_test_env")
    client = sync_client(fake)
    client.team.get()
    assert fake.requests[0].headers["authorization"] == f"Bearer {TEST_API_KEY}"
    client.close()


def test_caller_owned_http_client_is_not_closed(fake: FakeMCP) -> None:
    http_client = httpx.Client(transport=httpx.MockTransport(fake))
    client = SuperBooks(api_key=TEST_API_KEY, http_client=http_client)
    client.close()
    assert not http_client.is_closed


def test_transport_rejects_an_empty_key() -> None:
    with pytest.raises(ValueError, match="API key is required"):
        SyncTransport("", "https://api.superbooks.io")


def test_sse_responses_are_parsed(fake: FakeMCP) -> None:
    fake.sse = True
    fake.results["team_get"] = {"name": "Acme"}
    client = sync_client(fake)
    assert client.team.get() == {"name": "Acme"}
    client.close()
