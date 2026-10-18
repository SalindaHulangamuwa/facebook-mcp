"""Composition root: wires configuration, Graph client, Pages, services and tools."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

import httpx
from fastmcp import FastMCP
from fastmcp.server.auth import AuthProvider
from fastmcp.server.lifespan import lifespan

from facebook_mcp import __version__
from facebook_mcp.config import FacebookSettings
from facebook_mcp.graph import GraphClient
from facebook_mcp.pages import PageDirectory, page_source_from_settings
from facebook_mcp.services import Services
from facebook_mcp.tools import WRITE_TAG, register_all

SERVER_NAME = "facebook-mcp"

INSTRUCTIONS = """\
Manage Facebook Pages through the Graph API.
- Call list_pages to see which Pages are available. Every other tool takes an
  optional `page` (id or exact name); omit it to use the default Page.
- List tools are paginated: pass `next_cursor` back as `after` to continue.
- Post ids look like '<pageid>_<postid>'; comment ids come from list_comments.
- Confirm with the user before publishing, editing, hiding or deleting anything.
"""


def build_server(
    settings: FacebookSettings,
    *,
    read_only: bool = False,
    auth: AuthProvider | None = None,
    http_transport: httpx.AsyncBaseTransport | None = None,
) -> FastMCP:
    """Create a fully wired FastMCP server.

    `http_transport` lets tests inject a mock Graph API without patching.
    """
    graph = GraphClient.from_settings(settings, transport=http_transport)
    pages = PageDirectory(
        page_source_from_settings(settings, graph), graph, default_page=settings.default_page
    )

    @lifespan
    async def graph_lifespan(_server: FastMCP) -> AsyncIterator[dict[str, Any]]:
        async with graph:
            yield {}

    mcp = FastMCP(
        name=SERVER_NAME,
        version=__version__,
        instructions=INSTRUCTIONS,
        website_url="https://github.com/SalindaHulangamuwa/facebook-mcp",
        lifespan=graph_lifespan,
        mask_error_details=True,
        auth=auth,
    )
    register_all(mcp, Services.create(pages))

    if read_only:
        mcp.disable(tags={WRITE_TAG})
    return mcp
