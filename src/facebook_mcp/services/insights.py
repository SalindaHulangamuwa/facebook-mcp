from __future__ import annotations

from collections.abc import Sequence
from datetime import date
from typing import Any, Literal

from facebook_mcp.domain import InsightMetric
from facebook_mcp.pages import PageSession
from facebook_mcp.services.base import PageAwareService

InsightPeriod = Literal["day", "week", "days_28", "month", "lifetime", "total_over_range"]

DEFAULT_PAGE_METRICS = ("page_post_engagements",)
DEFAULT_POST_METRICS = ("post_reactions_by_type_total", "post_clicks")


class InsightsService(PageAwareService):
    async def page_insights(
        self,
        metrics: Sequence[str] = DEFAULT_PAGE_METRICS,
        period: InsightPeriod = "day",
        since: date | None = None,
        until: date | None = None,
        page: str | None = None,
    ) -> list[InsightMetric]:
        session = await self.pages.resolve(page)
        params = {
            "metric": ",".join(metrics),
            "period": period,
            "since": since.isoformat() if since else None,
            "until": until.isoformat() if until else None,
        }
        return await _insights(session, session.id, params)

    async def post_insights(
        self, post_id: str, metrics: Sequence[str] = DEFAULT_POST_METRICS, page: str | None = None
    ) -> list[InsightMetric]:
        session = await self.pages.resolve(page, object_id=post_id)
        return await _insights(session, post_id, {"metric": ",".join(metrics)})


async def _insights(
    session: PageSession, object_id: str, params: dict[str, Any]
) -> list[InsightMetric]:
    payload = await session.graph.get(f"{object_id}/insights", params)
    return [InsightMetric.model_validate(item) for item in payload.get("data", [])]
