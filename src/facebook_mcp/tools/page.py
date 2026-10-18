from __future__ import annotations

from fastmcp import FastMCP

from facebook_mcp.domain import PageInfo, PageSummary
from facebook_mcp.services import PageService
from facebook_mcp.tools.common import READ_ONLY, PageRef, tool


def register(mcp: FastMCP, pages: PageService) -> None:
    @tool(mcp, annotations=READ_ONLY)
    async def list_pages() -> list[PageSummary]:
        """List the Facebook Pages this server can manage (id and name)."""
        return await pages.list_pages()

    @tool(mcp, annotations=READ_ONLY)
    async def get_page_info(page: PageRef = None) -> PageInfo:
        """Get a Page's profile: name, category, about, link and audience size."""
        return await pages.get_info(page)
