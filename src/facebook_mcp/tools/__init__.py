"""MCP adapter layer: thin tool definitions that delegate to services."""

from __future__ import annotations

from fastmcp import FastMCP

from facebook_mcp.services import Services
from facebook_mcp.tools import comments, insights, page, posts
from facebook_mcp.tools.common import WRITE_TAG


def register_all(mcp: FastMCP, services: Services) -> None:
    page.register(mcp, services.page)
    posts.register(mcp, services.posts)
    comments.register(mcp, services.comments)
    insights.register(mcp, services.insights)


__all__ = ["WRITE_TAG", "register_all"]
