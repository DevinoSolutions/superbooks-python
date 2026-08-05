# SuperBooks Python SDK

Official Python client for [SuperBooks](https://superbooks.io) — typed access to
your accounting data.

The SDK talks to the SuperBooks API at `api.superbooks.io` over streamable
HTTP. Every one of the 45 tools is exposed as a typed method grouped by domain,
so you get autocomplete and type checking instead of stringly-typed tool calls.

- **Docs:** <https://docs.superbooks.io>
- **Requires:** Python 3.10+
- **Dependencies:** `httpx` — that is the whole list.

## Install

```bash
pip install superbooks
```

## Authentication

Mint an API key in SuperBooks under **Settings → Developer**. Keys are
`sb_`-prefixed and scoped at mint time — see [Scopes](#scopes-and-destructive-tools).
There is no separate test-mode key: every key is live and acts on real data.

```bash
export SUPERBOOKS_API_KEY="sb_your_api_key_here"
```

The client reads `SUPERBOOKS_API_KEY` automatically, or you can pass
`api_key=` explicitly.

## Quickstart (sync)

```python
from superbooks import SuperBooks

sb = SuperBooks()  # reads SUPERBOOKS_API_KEY

# Every tool is a typed method on its domain namespace.
page = sb.transactions.list(limit=10, status="posted")
for txn in page["items"]:
    print(txn["date"], txn["name"], txn["amount"], txn["currency"])

print(sb.reports.runway())
print(sb.reports.burn_rate(from_="2026-01-01", to="2026-06-30"))

invoice = sb.invoices.create_draft(
    customer_id="00000000-0000-0000-0000-000000000000",
    currency="USD",
    issue_date="2026-08-01",
    due_date="2026-08-31",
    line_items=[{"name": "Consulting", "quantity": 10, "price": 150.0}],
)

sb.close()  # or use `with SuperBooks() as sb:`
```

> **Note on `from_`.** `from` is a Python keyword, so parameters named `from` in
> the API are exposed as `from_`. The SDK sends the correct wire name.

## Quickstart (async)

`AsyncSuperBooks` is a mirror of `SuperBooks` — same namespaces, same method
names, same arguments — with every call awaited.

```python
import asyncio
from superbooks import AsyncSuperBooks


async def main() -> None:
    async with AsyncSuperBooks() as sb:
        page = await sb.transactions.list(limit=10)
        runway = await sb.reports.runway()
        print(len(page["items"]), runway)


asyncio.run(main())
```

## Tool surface

| Namespace            | Tools | Examples                                            |
| -------------------- | ----- | --------------------------------------------------- |
| `sb.transactions`    | 5     | `list`, `get`, `update_category`, `delete`          |
| `sb.invoices`        | 5     | `list`, `create_draft`, `send`, `void`              |
| `sb.customers`       | 5     | `list`, `create`, `update`, `delete`                |
| `sb.categories`      | 4     | `list`, `create`, `update`, `delete`                |
| `sb.tags`            | 3     | `list`, `create`, `delete`                          |
| `sb.documents`       | 4     | `list`, `get`, `search`, `delete`                   |
| `sb.inbox`           | 3     | `list`, `match`, `delete`                           |
| `sb.tracker`         | 5     | `list_projects`, `start_timer`, `stop_timer`        |
| `sb.bank_accounts`   | 1     | `list`                                              |
| `sb.team`            | 1     | `get`                                               |
| `sb.search`          | 1     | `global_`                                           |
| `sb.reports`         | 8     | `runway`, `burn_rate`, `profit_loss`, `revenue`     |

Methods return the tool's structured content when it provides any, and the raw
content blocks otherwise.

### Escape hatches

New tools land on the server before they land in a release. Reach them directly:

```python
sb.tools.list()  # every tool your key can see
sb.tools.call("transactions_list", {"limit": 5})  # call anything by name
```

`tools.list()` is scope-filtered server-side, so a read-only key genuinely does
not see write or destructive tools.

## Scopes and destructive tools

A key's scopes are fixed at mint time and enforced server-side — the SDK does
not filter anything locally. Two forms exist:

- **Meta-scopes**: `apis.all` (every resource, read and write) and `apis.read`
  (every resource, read only).
- **Fine-grained**: `<resource>.<read|write>`, e.g. `transactions.read`,
  `invoices.write`, `bank-accounts.read`.

The mint UI presents these as **All** (`apis.all`), **Read Only**
(`apis.read`), and **Restricted** (pick individual resource scopes).

### What your scopes actually grant on the API

Read this before assuming a narrow key is a sandbox.

Scopes are the vocabulary for the **whole SuperBooks API**, not just the tools
this SDK exposes. At the tool layer they collapse into three coarse tiers —
read, write, and destructive — and **the tier, not the resource, is what gates
a tool**:

| Your scopes                                 | What you can reach                 |
| ------------------------------------------- | ---------------------------------- |
| any `<resource>.read` (or `apis.read`)      | **every** read tool                |
| any `<resource>.write`                      | **every** read and write tool      |
| `apis.all` + team setting enabled           | every tool, including destructive  |

So a key scoped only `tags.write` can still call `invoices_send` and
`customers_update` — the `tags` part narrows nothing once the write tier is
unlocked. If you want a key that genuinely cannot write, give it only `.read`
scopes (or `apis.read`).

Two consequences of scopes being the full-API vocabulary:

- `users` and `notifications` scopes exist but have no tools behind them.
- There is no `categories` scope at all, yet the four `categories_*` tools are
  reachable — they ride the coarse read/write/destructive tier like everything
  else.

### Destructive tools

`transactions.delete`, `invoices.void`, `customers.delete`,
`categories.delete`, `tags.delete`, `documents.delete`, `inbox.delete`, and
`tracker.delete_entry` sit behind **two** gates that must both be open:

1. the credential carries the full-access `apis.all` scope, **and**
2. the team has destructive AI tools enabled in its settings.

This is the one place the coarse tiering is deliberately tightened: a
fine-grained `<resource>.write` scope is *not* enough, so a leaked narrow key
can never delete. Missing either gate means the tool is absent from
`tools.list()` and calling it raises `AuthorizationError`.

## Errors

```python
from superbooks import (
    SuperBooksError,  # base class — catch this to catch everything
    APIError,  # non-2xx response
    AuthenticationError,  # 401 — bad or revoked key
    AuthorizationError,  # 403 — valid key, insufficient scope / no team
    RateLimitError,  # 429 — carries .retry_after
    ConnectionError,  # never reached the API
    ProtocolError,  # reply was not valid MCP/JSON-RPC
    ToolError,  # tool ran and reported failure
)

try:
    sb.transactions.list()
except RateLimitError as exc:
    print(f"slow down for {exc.retry_after}s")
except SuperBooksError as exc:
    print(f"request failed: {exc}")
```

### Retries

Automatic retry on 429 is **off by default** (`max_retries=0`). The API's
`Retry-After` is a full 60 seconds, and silently parking a caller for minutes is
worse than raising. Opt in when you want it:

```python
sb = SuperBooks(max_retries=2)  # each sleep honours Retry-After, capped at 60s
```

Nothing else is retried automatically — a failed write stays failed rather than
being replayed.

## Connecting an agent client

SuperBooks hosts a remote tool server at `https://api.superbooks.io/mcp`. Any
agent client that can call a remote server with a custom header can connect to
it directly with your API key — the SDK is not involved, and nothing needs to
run locally. For example, with Claude Code:

```bash
claude mcp add --transport http superbooks https://api.superbooks.io/mcp \
  --header "Authorization: Bearer sb_your_api_key_here"
```

The same scopes and tiers described above apply. See
<https://docs.superbooks.io> for the full setup guide.

## Configuration

| Argument      | Env var               | Default                      |
| ------------- | --------------------- | ---------------------------- |
| `api_key`     | `SUPERBOOKS_API_KEY`  | — (required)                 |
| `base_url`    | `SUPERBOOKS_BASE_URL` | `https://api.superbooks.io`  |
| `timeout`     | —                     | `60.0` seconds               |
| `max_retries` | —                     | `0`                          |
| `http_client` | —                     | a client the SDK owns        |

Passing your own `httpx.Client` / `httpx.AsyncClient` (for proxies or custom
transports) leaves ownership with you — `close()` won't close it.

## Development

```bash
pip install -e ".[dev]"

python scripts/codegen.py          # regenerate namespaces from sdk-manifest.json
python scripts/codegen.py --check  # CI gate: fails if they are out of date

ruff check . && ruff format --check .
mypy
pytest
```

`src/superbooks/_generated/` is machine-written from `sdk-manifest.json` — edit
the manifest and regenerate rather than editing those files. Tests never make
network calls; they run against `httpx.MockTransport`.

## License

MIT — see [LICENSE](LICENSE).
