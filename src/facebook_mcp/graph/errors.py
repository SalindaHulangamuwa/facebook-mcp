"""Exception hierarchy that turns Graph API failures into actionable messages."""

from __future__ import annotations

from typing import Any, ClassVar

import httpx

from facebook_mcp.exceptions import FacebookMCPError

_RATE_LIMIT_CODES = frozenset({4, 17, 32, 613})
_PERMISSION_CODES = frozenset({10, *range(200, 300)})
_AUTH_CODES = frozenset({102, 190})


class GraphAPIError(FacebookMCPError):
    """A request to the Graph API failed."""

    hint: ClassVar[str] = "Check the request parameters and try again."

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        code: int | None = None,
        subcode: int | None = None,
        fbtrace_id: str | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.code = code
        self.subcode = subcode
        self.fbtrace_id = fbtrace_id

    @property
    def user_message(self) -> str:
        """Message safe to show the AI client: what failed and what to do about it."""
        code = f" (code {self.code})" if self.code is not None else ""
        return f"Facebook API error{code}: {self.message}. {self.hint}"


class GraphAuthError(GraphAPIError):
    hint = "The access token is invalid or expired. Generate a new Page access token."


class GraphPermissionError(GraphAPIError):
    hint = "The token lacks a required permission. Re-generate it with the needed scopes."


class GraphRateLimitError(GraphAPIError):
    hint = "Rate limit reached. Wait a few minutes before retrying."


class GraphConnectionError(GraphAPIError):
    hint = "Could not reach graph.facebook.com. Check network connectivity."


def _error_class_for(code: int | None) -> type[GraphAPIError]:
    if code in _AUTH_CODES:
        return GraphAuthError
    if code in _RATE_LIMIT_CODES:
        return GraphRateLimitError
    if code in _PERMISSION_CODES:
        return GraphPermissionError
    return GraphAPIError


def _error_payload(response: httpx.Response) -> dict[str, Any]:
    try:
        body = response.json()
    except ValueError:
        return {}
    return body.get("error", {}) if isinstance(body, dict) else {}


def error_from_response(response: httpx.Response) -> GraphAPIError:
    """Build the most specific error type for a failed Graph API response."""
    payload = _error_payload(response)
    code = payload.get("code")
    message = payload.get("error_user_msg") or payload.get("message") or response.reason_phrase
    return _error_class_for(code)(
        message,
        status_code=response.status_code,
        code=code,
        subcode=payload.get("error_subcode"),
        fbtrace_id=payload.get("fbtrace_id"),
    )
