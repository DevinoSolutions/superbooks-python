"""The generated surface matches the manifest, and stays matched.

`test_generated_files_are_current` is the load-bearing one: it re-runs the
generator in memory and byte-compares, so a hand-edit to `_generated/` or a
manifest update without regeneration fails CI.
"""

from __future__ import annotations

import inspect
import json
import sys
from pathlib import Path

import pytest

from superbooks._generated import DOMAINS, TOOL_COUNT
from superbooks._generated._async import AsyncReports, AsyncTransactions
from superbooks._generated._sync import Invoices, Reports, Search, Transactions

from .conftest import FakeMCP, sync_client

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import codegen  # noqa: E402


@pytest.fixture(scope="module")
def manifest() -> dict:
    return json.loads((REPO_ROOT / "sdk-manifest.json").read_text(encoding="utf-8"))


def test_generated_files_are_current(manifest: dict) -> None:
    for path, expected in codegen.generate(manifest).items():
        assert path.exists(), f"{path} is missing — run scripts/codegen.py"
        actual = path.read_text(encoding="utf-8")
        assert actual == expected, (
            f"{path.name} is out of date with sdk-manifest.json. "
            "Run `python scripts/codegen.py` and commit the result."
        )


def test_tool_count_matches_the_manifest(manifest: dict) -> None:
    assert manifest["toolCount"] == TOOL_COUNT
    assert sum(len(v) for v in manifest["domains"].values()) == TOOL_COUNT


def test_every_manifest_domain_is_a_namespace(manifest: dict) -> None:
    assert set(DOMAINS) == set(manifest["domains"])


def test_every_manifest_tool_has_a_method(manifest: dict) -> None:
    for domain, tools in manifest["domains"].items():
        sync_cls, async_cls = DOMAINS[domain]
        for tool in tools:
            method = codegen.method_name_for(domain, tool["name"])
            assert hasattr(sync_cls, method), f"{domain}.{method} missing (sync)"
            assert hasattr(async_cls, method), f"{domain}.{method} missing (async)"


# --- Snapshots for three representative domains ------------------------------


def test_transactions_signatures() -> None:
    # `from __future__ import annotations` stores the unparsed AST, so string
    # literals come back single-quoted here regardless of the source style.
    assert str(inspect.signature(Transactions.list)) == (
        "(self, *, from_: 'str | None' = None, to: 'str | None' = None, "
        "status: \"Literal['posted', 'pending', 'excluded', 'completed', "
        "'archived', 'exported'] | None\" = None, "
        "category_slug: 'str | None' = None, "
        "bank_account_id: 'str | None' = None, cursor: 'str | None' = None, "
        "limit: 'int | None' = None) -> 'Any'"
    )
    assert str(inspect.signature(Transactions.get)) == "(self, id: 'str') -> 'Any'"
    assert (
        str(inspect.signature(Transactions.update_category))
        == "(self, id: 'str', category_slug: 'str') -> 'Any'"
    )


def test_invoices_signatures() -> None:
    assert str(inspect.signature(Invoices.create_draft)) == (
        "(self, customer_id: 'str', currency: 'str', issue_date: 'str', "
        "due_date: 'str', line_items: 'builtins.list[builtins.dict[str, Any]]', "
        "*, note: 'str | None' = None) -> 'Any'"
    )
    assert str(inspect.signature(Invoices.void)) == "(self, id: 'str') -> 'Any'"


def test_reports_signatures() -> None:
    assert (
        str(inspect.signature(Reports.burn_rate))
        == "(self, from_: 'str', to: 'str') -> 'Any'"
    )
    assert str(inspect.signature(Reports.runway)) == "(self) -> 'Any'"


def test_required_arguments_may_be_positional() -> None:
    kinds = [
        p.kind
        for name, p in inspect.signature(Invoices.create_draft).parameters.items()
        if name != "self"
    ]
    assert kinds[0] is inspect.Parameter.POSITIONAL_OR_KEYWORD  # customer_id
    assert kinds[-1] is inspect.Parameter.KEYWORD_ONLY  # note


def test_python_keywords_are_mangled_in_names() -> None:
    # `global` and `from` are keywords; the SDK exposes them with a trailing
    # underscore while the wire name stays intact (asserted below).
    assert hasattr(Search, "global_")
    assert not hasattr(Search, "global")
    assert "from_" in inspect.signature(Reports.burn_rate).parameters


def test_mangled_names_are_restored_on_the_wire() -> None:
    fake = FakeMCP()
    client = sync_client(fake)
    client.reports.burn_rate(from_="2026-01-01", to="2026-06-30")
    args = fake.tool_call_arguments("reports_burn_rate")
    assert args == {"from": "2026-01-01", "to": "2026-06-30"}
    assert "from_" not in args
    client.close()


def test_search_global_uses_the_unmangled_tool_name() -> None:
    fake = FakeMCP()
    client = sync_client(fake)
    client.search.global_("acme")
    assert fake.calls_to("tools/call")[0].body["params"]["name"] == "search_global"
    client.close()


def test_unset_arguments_are_omitted_not_nulled() -> None:
    fake = FakeMCP()
    client = sync_client(fake)
    client.transactions.list(limit=5)
    # Sending explicit nulls would override the server's own defaults.
    assert fake.tool_call_arguments("transactions_list") == {"limit": 5}
    client.close()


def test_destructive_tools_are_flagged_in_docstrings(manifest: dict) -> None:
    destructive = [
        (domain, tool["name"])
        for domain, tools in manifest["domains"].items()
        for tool in tools
        if tool["destructive"]
    ]
    assert destructive, "expected the manifest to contain destructive tools"
    for domain, tool_name in destructive:
        sync_cls, _ = DOMAINS[domain]
        method = getattr(sync_cls, codegen.method_name_for(domain, tool_name))
        assert "Destructive" in (method.__doc__ or ""), tool_name


def test_async_namespace_methods_are_coroutines() -> None:
    assert inspect.iscoroutinefunction(AsyncTransactions.list)
    assert inspect.iscoroutinefunction(AsyncReports.runway)
    assert not inspect.iscoroutinefunction(Transactions.list)
