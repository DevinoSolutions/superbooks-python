"""Base classes for the generated per-domain namespaces.

Hand-written on purpose: the generated modules under ``_generated/`` contain
nothing but the tool surface, so regenerating them can never disturb the
plumbing.
"""

from __future__ import annotations

from typing import Any

from ._protocol import prune_arguments
from ._transport import AsyncTransport, SyncTransport


class SyncNamespace:
    """A group of related tools on a :class:`~superbooks.SuperBooks` client."""

    def __init__(self, transport: SyncTransport) -> None:
        self._transport = transport

    def _call(self, tool: str, arguments: dict[str, Any]) -> Any:
        return self._transport.call_tool(tool, prune_arguments(arguments))


class AsyncNamespace:
    """A group of related tools on an :class:`~superbooks.AsyncSuperBooks` client."""

    def __init__(self, transport: AsyncTransport) -> None:
        self._transport = transport

    async def _call(self, tool: str, arguments: dict[str, Any]) -> Any:
        return await self._transport.call_tool(tool, prune_arguments(arguments))
