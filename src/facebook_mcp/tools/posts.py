from __future__ import annotations

from datetime import datetime
from typing import Annotated

from fastmcp import FastMCP
from pydantic import Field, HttpUrl

from facebook_mcp.domain import CreatedObject, OperationResult, Paginated, Post, PostDraft, ReelDraft
from facebook_mcp.services import PostService
from facebook_mcp.tools.common import (
    CREATES,
    MODIFIES,
    READ_ONLY,
    WRITE_TAG,
    Cursor,
    GraphId,
    Limit,
    Message,
    PageRef,
    tool,
)

OptionalText = Annotated[str | None, Field(max_length=63206)]
ScheduledTime = Annotated[
    datetime | None,
    Field(
        description=(
            "ISO-8601 time to publish later (10 minutes to 30 days ahead). "
            "Omit to publish immediately."
        )
    ),
]


def register(mcp: FastMCP, posts: PostService) -> None:
    @tool(mcp, annotations=READ_ONLY)
    async def list_posts(
        limit: Limit = 10, after: Cursor = None, page: PageRef = None
    ) -> Paginated[Post]:
        """List a Page's published posts, newest first, with engagement counts."""
        return await posts.list_posts(limit, after, page)

    @tool(mcp, annotations=READ_ONLY)
    async def list_scheduled_posts(
        limit: Limit = 10, after: Cursor = None, page: PageRef = None
    ) -> Paginated[Post]:
        """List a Page's posts that are scheduled but not yet published."""
        return await posts.list_scheduled_posts(limit, after, page)

    @tool(mcp, annotations=READ_ONLY)
    async def get_post(post_id: GraphId, page: PageRef = None) -> Post:
        """Get a single post with its message, permalink and engagement counts."""
        return await posts.get_post(post_id, page)

    @tool(mcp, annotations=CREATES, tags={WRITE_TAG})
    async def create_post(
        message: OptionalText = None,
        link: HttpUrl | None = None,
        scheduled_time: ScheduledTime = None,
        page: PageRef = None,
    ) -> CreatedObject:
        """Publish (or schedule) a text/link post on a Page. Needs a message, a link, or both."""
        draft = PostDraft(
            message=message, link=str(link) if link else None, scheduled_time=scheduled_time
        )
        return await posts.create_post(draft, page)

    @tool(mcp, annotations=CREATES, tags={WRITE_TAG})
    async def create_photo_post(
        image_url: Annotated[HttpUrl, Field(description="Publicly reachable image URL.")],
        caption: OptionalText = None,
        page: PageRef = None,
    ) -> CreatedObject:
        """Publish a photo post on a Page from a public image URL."""
        return await posts.create_photo_post(str(image_url), caption, page)

    @tool(mcp, annotations=CREATES, tags={WRITE_TAG})
    async def create_reel(
        video_path: Annotated[
            str, Field(min_length=1, description="Absolute path to a local 9:16 .mp4 file.")
        ],
        description: OptionalText = None,
        scheduled_time: ScheduledTime = None,
        page: PageRef = None,
    ) -> CreatedObject:
        """Upload a local video and publish (or schedule) it as a Reel on a Page."""
        draft = ReelDraft(
            video_path=video_path, description=description, scheduled_time=scheduled_time
        )
        return await posts.create_reel(draft, page)

    @tool(mcp, annotations=MODIFIES, tags={WRITE_TAG})
    async def update_post(
        post_id: GraphId, message: Message, page: PageRef = None
    ) -> OperationResult:
        """Replace the text of an existing Page post."""
        return await posts.update_post(post_id, message, page)

    @tool(mcp, annotations=MODIFIES, tags={WRITE_TAG})
    async def delete_post(post_id: GraphId, page: PageRef = None) -> OperationResult:
        """Permanently delete a Page post. This cannot be undone."""
        return await posts.delete_post(post_id, page)
