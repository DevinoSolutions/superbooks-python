"""Exception hierarchy for the SuperBooks SDK.

Every failure the SDK raises derives from :class:`SuperBooksError`, so callers
can catch one type and refine from there.
"""

from __future__ import annotations

__all__ = [
    "APIError",
    "AuthenticationError",
    "AuthorizationError",
    "ConnectionError",
    "ProtocolError",
    "RateLimitError",
    "SuperBooksError",
    "ToolError",
]


class SuperBooksError(Exception):
    """Base class for every error raised by this SDK."""


class APIError(SuperBooksError):
    """The API returned an unsuccessful HTTP response.

    Attributes:
        status_code: HTTP status code, or ``None`` if the failure happened
            before a response was received.
        body: Response body text, truncated by the caller if very large.
    """

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        body: str | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.body = body


class AuthenticationError(APIError):
    """HTTP 401 — the API key is missing, malformed, or has been revoked."""


class AuthorizationError(APIError):
    """HTTP 403 — the credential is valid but not allowed to do this.

    Named ``AuthorizationError`` rather than ``PermissionError`` so it does not
    shadow the Python builtin of that name.
    """


class RateLimitError(APIError):
    """HTTP 429 — too many requests for this credential.

    Attributes:
        retry_after: Seconds to wait before retrying, parsed from the
            ``Retry-After`` response header, or ``None`` if absent/unparseable.
    """

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = 429,
        body: str | None = None,
        retry_after: float | None = None,
    ) -> None:
        super().__init__(message, status_code=status_code, body=body)
        self.retry_after = retry_after


class ConnectionError(SuperBooksError):  # noqa: A001 - deliberate SDK-scoped name
    """The request never completed: DNS, TCP, TLS, or timeout failure."""


class ProtocolError(SuperBooksError):
    """The server replied, but not with something valid for MCP/JSON-RPC."""


class ToolError(SuperBooksError):
    """A tool was reached but reported failure.

    Raised both for JSON-RPC ``error`` objects and for tool results flagged
    with ``isError``.

    Attributes:
        code: JSON-RPC error code, when the failure came from one.
        data: Any structured payload the server attached to the error.
    """

    def __init__(
        self,
        message: str,
        *,
        code: int | None = None,
        data: object | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.data = data
