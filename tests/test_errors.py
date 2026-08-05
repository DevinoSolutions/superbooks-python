"""HTTP status and JSON-RPC failures map onto the SDK error hierarchy."""

from __future__ import annotations

import httpx
import pytest

from superbooks import (
    APIError,
    AuthenticationError,
    AuthorizationError,
    ConnectionError,
    ProtocolError,
    RateLimitError,
    SuperBooksError,
    ToolError,
)
from superbooks._protocol import parse_retry_after

from .conftest import TEST_API_KEY, FakeMCP, sync_client


@pytest.mark.parametrize(
    ("status", "expected"),
    [
        (401, AuthenticationError),
        (403, AuthorizationError),
        (429, RateLimitError),
        (400, APIError),
        (500, APIError),
        (503, APIError),
    ],
)
def test_status_codes_map_to_error_types(
    status: int, expected: type[Exception]
) -> None:
    fake = FakeMCP(status=status)
    client = sync_client(fake)
    with pytest.raises(expected) as info:
        client.team.get()
    assert info.value.status_code == status  # type: ignore[attr-defined]
    client.close()


def test_every_error_derives_from_the_base_class() -> None:
    for cls in (
        APIError,
        AuthenticationError,
        AuthorizationError,
        RateLimitError,
        ConnectionError,
        ProtocolError,
        ToolError,
    ):
        assert issubclass(cls, SuperBooksError)


def test_authorization_error_does_not_shadow_the_builtin() -> None:
    # A caller catching the builtin PermissionError must not accidentally
    # swallow ours, and vice versa.
    assert AuthorizationError is not PermissionError
    assert not issubclass(AuthorizationError, PermissionError)


def test_rate_limit_error_exposes_retry_after() -> None:
    fake = FakeMCP(status=429, response_headers={"Retry-After": "60"})
    client = sync_client(fake)
    with pytest.raises(RateLimitError) as info:
        client.team.get()
    assert info.value.retry_after == 60.0
    client.close()


def test_rate_limit_without_a_header_has_no_retry_after() -> None:
    fake = FakeMCP(status=429)
    client = sync_client(fake)
    with pytest.raises(RateLimitError) as info:
        client.team.get()
    assert info.value.retry_after is None
    client.close()


@pytest.mark.parametrize(
    ("header", "expected"),
    [
        ("60", 60.0),
        (" 30 ", 30.0),
        ("0", 0.0),
        ("later", None),
        ("-5", None),
        (None, None),
    ],
)
def test_retry_after_parsing(header: str | None, expected: float | None) -> None:
    assert parse_retry_after(header) == expected


def test_retries_are_off_by_default() -> None:
    fake = FakeMCP(status=429, fail_times=1, response_headers={"Retry-After": "0"})
    client = sync_client(fake)
    with pytest.raises(RateLimitError):
        client.team.get()
    assert len(fake.requests) == 1
    client.close()


def test_bounded_retry_recovers_when_opted_in() -> None:
    fake = FakeMCP(status=429, fail_times=1, response_headers={"Retry-After": "0"})
    client = sync_client(fake, max_retries=2)
    assert client.team.get() == {"ok": True, "tool": "team_get"}
    client.close()


def test_retry_gives_up_after_the_bound() -> None:
    fake = FakeMCP(status=429, fail_times=99, response_headers={"Retry-After": "0"})
    client = sync_client(fake, max_retries=2)
    with pytest.raises(RateLimitError):
        client.team.get()
    # Original attempt plus two retries.
    assert len(fake.requests) == 3
    client.close()


def test_network_failure_becomes_connection_error() -> None:
    def explode(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("no route to host")

    from superbooks import SuperBooks

    client = SuperBooks(
        api_key=TEST_API_KEY,
        http_client=httpx.Client(transport=httpx.MockTransport(explode)),
    )
    with pytest.raises(ConnectionError, match="Could not reach"):
        client.team.get()
    client.close()


def test_jsonrpc_error_becomes_tool_error() -> None:
    fake = FakeMCP(
        jsonrpc_error={"code": -32602, "message": "Invalid params", "data": {"x": 1}}
    )
    client = sync_client(fake)
    with pytest.raises(ToolError) as info:
        client.transactions.get("abc")
    assert info.value.code == -32602
    assert info.value.data == {"x": 1}
    assert "Invalid params" in str(info.value)
    client.close()


def test_tool_flagged_is_error_raises_with_its_text() -> None:
    fake = FakeMCP(tool_is_error=True, results={"team_get": {"why": "no team"}})
    client = sync_client(fake)
    with pytest.raises(ToolError, match="no team"):
        client.team.get()
    client.close()


def test_non_json_response_becomes_protocol_error() -> None:
    def html(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200, headers={"content-type": "text/html"}, text="<html>hi</html>"
        )

    from superbooks import SuperBooks

    client = SuperBooks(
        api_key=TEST_API_KEY,
        http_client=httpx.Client(transport=httpx.MockTransport(html)),
    )
    with pytest.raises(ProtocolError):
        client.team.get()
    client.close()


def test_error_body_is_truncated_not_unbounded() -> None:
    def huge(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text="x" * 10_000)

    from superbooks import SuperBooks

    client = SuperBooks(
        api_key=TEST_API_KEY,
        http_client=httpx.Client(transport=httpx.MockTransport(huge)),
    )
    with pytest.raises(APIError) as info:
        client.team.get()
    assert info.value.body is not None
    assert len(info.value.body) < 10_000
    assert "truncated" in info.value.body
    client.close()
