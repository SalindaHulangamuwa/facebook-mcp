from __future__ import annotations

from facebook_mcp.exceptions import FacebookMCPError


class PageNotFoundError(FacebookMCPError):
    """No Page matches the requested id or name."""


class PageSelectionError(FacebookMCPError):
    """Several Pages are available and the request did not say which one to use."""
