"""Which Pages the server can act on, and how a tool call picks one."""

from facebook_mcp.pages.directory import PageDirectory
from facebook_mcp.pages.errors import PageNotFoundError, PageSelectionError
from facebook_mcp.pages.models import PageCredential, PageSession
from facebook_mcp.pages.sources import (
    AccountsPageSource,
    PageSource,
    StaticPageSource,
    page_source_from_settings,
)

__all__ = [
    "AccountsPageSource",
    "PageCredential",
    "PageDirectory",
    "PageNotFoundError",
    "PageSelectionError",
    "PageSession",
    "PageSource",
    "StaticPageSource",
    "page_source_from_settings",
]
