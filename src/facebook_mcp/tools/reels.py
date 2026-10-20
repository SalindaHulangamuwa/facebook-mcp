from __future__ import annotations

from pathlib import Path
from typing import Annotated

from fastmcp import Context, FastMCP
from pydantic import Field

from facebook_mcp.domain import CreatedObject, ReelDraft
from facebook_mcp.services import PostService
from facebook_mcp.services.uploads import ProgressCallback
from facebook_mcp.tools.common import CREATES, WRITE_TAG, PageRef, tool
from facebook_mcp.tools.posts import OptionalText, ScheduledTime

MB = 1024 * 1024

VideoPath = Annotated[
    str, Field(min_length=1, description="Absolute path to a local 9:16 .mp4 file.")
]


def register(mcp: FastMCP, posts: PostService) -> None:
    @tool(mcp, annotations=CREATES, tags={WRITE_TAG})
    async def create_reel(
        ctx: Context,
        video_path: VideoPath,
        description: OptionalText = None,
        scheduled_time: ScheduledTime = None,
        page: PageRef = None,
    ) -> CreatedObject:
        """Upload a local video and publish (or schedule) it as a Reel on a Page.

        Large videos can take several minutes; upload progress is reported to the client.
        """
        draft = ReelDraft(
            video_path=Path(video_path), description=description, scheduled_time=scheduled_time
        )
        return await posts.create_reel(draft, page, _progress_reporter(ctx))


def _progress_reporter(ctx: Context) -> ProgressCallback:
    async def report(sent: int, total: int) -> None:
        await ctx.report_progress(sent, total, f"Uploaded {sent / MB:.1f} of {total / MB:.1f} MB")

    return report
