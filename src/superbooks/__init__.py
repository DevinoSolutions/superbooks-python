"""Official SuperBooks SDK for Python.

Talks to the SuperBooks API at api.superbooks.io over streamable HTTP, exposing
every tool as a typed method grouped by domain::

    from superbooks import SuperBooks

    sb = SuperBooks(api_key="sb_your_api_key_here")
    print(sb.reports.runway())
"""

from __future__ import annotations

from ._client import AsyncSuperBooks, SuperBooks
from ._errors import (
    APIError,
    AuthenticationError,
    AuthorizationError,
    ConnectionError,
    ProtocolError,
    RateLimitError,
    SuperBooksError,
    ToolError,
)
from ._generated import TOOL_COUNT
from ._version import __version__

__all__ = [
    "TOOL_COUNT",
    "APIError",
    "AsyncSuperBooks",
    "AuthenticationError",
    "AuthorizationError",
    "ConnectionError",
    "ProtocolError",
    "RateLimitError",
    "SuperBooks",
    "SuperBooksError",
    "ToolError",
    "__version__",
]
