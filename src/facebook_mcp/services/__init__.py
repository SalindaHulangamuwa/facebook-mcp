"""Service layer: Page-level use cases expressed in domain terms."""

from __future__ import annotations

from dataclasses import dataclass

from facebook_mcp.pages import PageDirectory
from facebook_mcp.services.comments import CommentService
from facebook_mcp.services.insights import InsightsService
from facebook_mcp.services.page import PageService
from facebook_mcp.services.posts import PostService


@dataclass(frozen=True)
class Services:
    """Every service the tools depend on, built from one shared `PageDirectory`."""

    page: PageService
    posts: PostService
    comments: CommentService
    insights: InsightsService

    @classmethod
    def create(cls, pages: PageDirectory) -> Services:
        return cls(
            page=PageService(pages),
            posts=PostService(pages),
            comments=CommentService(pages),
            insights=InsightsService(pages),
        )


__all__ = ["CommentService", "InsightsService", "PageService", "PostService", "Services"]
