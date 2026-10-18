from __future__ import annotations

from datetime import date
from typing import Annotated

from fastmcp import FastMCP
from pydantic import Field

from facebook_mcp.domain import InsightMetric
from facebook_mcp.services import InsightsService
from facebook_mcp.services.insights import (
    DEFAULT_PAGE_METRICS,
    DEFAULT_POST_METRICS,
    InsightPeriod,
)
from facebook_mcp.tools.common import READ_ONLY, GraphId, PageRef, tool

Metrics = Annotated[
    list[str] | None,
    Field(min_length=1, description="Graph insights metric names. Omit to use the defaults."),
]


def register(mcp: FastMCP, insights: InsightsService) -> None:
    @tool(mcp, annotations=READ_ONLY)
    async def get_page_insights(
        metrics: Metrics = None,
        period: InsightPeriod = "day",
        since: date | None = None,
        until: date | None = None,
        page: PageRef = None,
    ) -> list[InsightMetric]:
        """Get Page-level analytics (default: post engagements) for a period and date range."""
        return await insights.page_insights(
            metrics or DEFAULT_PAGE_METRICS, period, since, until, page
        )

    @tool(mcp, annotations=READ_ONLY)
    async def get_post_insights(
        post_id: GraphId, metrics: Metrics = None, page: PageRef = None
    ) -> list[InsightMetric]:
        """Get analytics for one post (default: reactions by type and clicks)."""
        return await insights.post_insights(post_id, metrics or DEFAULT_POST_METRICS, page)
