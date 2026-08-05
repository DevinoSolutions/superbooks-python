# Changelog

All notable changes to this project are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-08-04

Initial release.

### Added

- `SuperBooks` sync client and `AsyncSuperBooks` async client, sharing one
  streamable-HTTP protocol core over `httpx`.
- Typed methods for all 45 tools across 12 domains (`transactions`, `invoices`,
  `customers`, `categories`, `tags`, `documents`, `inbox`, `tracker`,
  `bank_accounts`, `team`, `search`, `reports`), generated from
  `sdk-manifest.json` by `scripts/codegen.py`.
- Error hierarchy rooted at `SuperBooksError`: `APIError`,
  `AuthenticationError` (401), `AuthorizationError` (403), `RateLimitError`
  (429, with `retry_after`), `ConnectionError`, `ProtocolError`, `ToolError`.
- Opt-in bounded retry on 429, disabled by default.
- `sb.tools.list()` / `sb.tools.call()` escape hatches for tools not yet in a
  released namespace.
- `py.typed` marker; the package ships its own type information.

[Unreleased]: https://github.com/DevinoSolutions/superbooks-python/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/DevinoSolutions/superbooks-python/releases/tag/v0.1.0
