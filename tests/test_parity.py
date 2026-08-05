"""The async client is a faithful mirror of the sync one."""

from __future__ import annotations

import inspect

import pytest

from superbooks import AsyncSuperBooks, SuperBooks
from superbooks._generated import DOMAINS

from .conftest import FakeMCP, async_client, sync_client


def _public_methods(cls: type) -> set[str]:
    return {
        name
        for name, value in vars(cls).items()
        if not name.startswith("_") and callable(value)
    }


def test_namespaces_expose_identical_method_names() -> None:
    for domain, (sync_cls, async_cls) in DOMAINS.items():
        assert _public_methods(sync_cls) == _public_methods(async_cls), domain


def test_namespace_signatures_are_identical() -> None:
    for domain, (sync_cls, async_cls) in DOMAINS.items():
        for name in _public_methods(sync_cls):
            sync_sig = inspect.signature(getattr(sync_cls, name))
            async_sig = inspect.signature(getattr(async_cls, name))
            assert sync_sig == async_sig, f"{domain}.{name}"


def test_clients_expose_the_same_namespaces() -> None:
    fake = FakeMCP()
    sync = sync_client(fake)
    a_sync = async_client(fake)
    for domain in DOMAINS:
        assert hasattr(sync, domain)
        assert hasattr(a_sync, domain)
    assert hasattr(sync, "tools")
    assert hasattr(a_sync, "tools")
    sync.close()


def test_tools_escape_hatch_has_matching_surfaces() -> None:
    from superbooks._client import AsyncTools, SyncTools

    assert _public_methods(SyncTools) == _public_methods(AsyncTools) == {"list", "call"}


async def test_async_and_sync_return_the_same_payload() -> None:
    payload = {"items": [{"id": "t1", "amount": 12.5}], "nextCursor": None}

    sync_fake = FakeMCP(results={"transactions_list": payload})
    sync = sync_client(sync_fake)
    sync_result = sync.transactions.list(limit=1)
    sync.close()

    async_fake = FakeMCP(results={"transactions_list": payload})
    async with async_client(async_fake) as asb:
        async_result = await asb.transactions.list(limit=1)

    assert sync_result == async_result == payload


async def test_async_and_sync_send_identical_requests() -> None:
    sync_fake = FakeMCP()
    sync = sync_client(sync_fake)
    sync.reports.burn_rate(from_="2026-01-01", to="2026-03-31")
    sync.close()

    async_fake = FakeMCP()
    async with async_client(async_fake) as asb:
        await asb.reports.burn_rate(from_="2026-01-01", to="2026-03-31")

    assert [r.method for r in sync_fake.requests] == [
        r.method for r in async_fake.requests
    ]
    assert sync_fake.tool_call_arguments(
        "reports_burn_rate"
    ) == async_fake.tool_call_arguments("reports_burn_rate")


async def test_async_handshake_runs_once() -> None:
    fake = FakeMCP()
    async with async_client(fake) as asb:
        await asb.team.get()
        await asb.team.get()
    assert len(fake.calls_to("initialize")) == 1


async def test_async_errors_map_the_same_way() -> None:
    from superbooks import AuthenticationError

    fake = FakeMCP(status=401)
    async with async_client(fake) as asb:
        with pytest.raises(AuthenticationError):
            await asb.team.get()


async def test_async_sse_is_parsed() -> None:
    fake = FakeMCP(sse=True, results={"team_get": {"name": "Acme"}})
    async with async_client(fake) as asb:
        assert await asb.team.get() == {"name": "Acme"}


def test_sync_context_manager_closes(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SUPERBOOKS_API_KEY", "sb_your_api_key_here")
    with SuperBooks() as client:
        assert isinstance(client, SuperBooks)


async def test_async_context_manager_closes(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SUPERBOOKS_API_KEY", "sb_your_api_key_here")
    async with AsyncSuperBooks() as client:
        assert isinstance(client, AsyncSuperBooks)


async def test_tools_escape_hatch_round_trips() -> None:
    fake = FakeMCP(tools=[{"name": "transactions_list", "description": "…"}])
    sync = sync_client(fake)
    assert sync.tools.list() == [{"name": "transactions_list", "description": "…"}]
    sync.tools.call("transactions_list", {"limit": 3})
    assert fake.tool_call_arguments("transactions_list") == {"limit": 3}
    sync.close()

    async_fake = FakeMCP(tools=[{"name": "transactions_list", "description": "…"}])
    async with async_client(async_fake) as asb:
        assert await asb.tools.list() == [
            {"name": "transactions_list", "description": "…"}
        ]
        await asb.tools.call("transactions_list", {"limit": 3})
    assert async_fake.tool_call_arguments("transactions_list") == {"limit": 3}
