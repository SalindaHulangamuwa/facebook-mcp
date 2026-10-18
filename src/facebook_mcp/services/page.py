from __future__ import annotations

from facebook_mcp.domain import PageInfo, PageSummary
from facebook_mcp.services.base import PageAwareService, fields

PAGE_FIELDS = fields("id", "name", "category", "about", "link", "fan_count", "followers_count")


class PageService(PageAwareService):
    async def list_pages(self) -> list[PageSummary]:
        return [PageSummary(id=page.id, name=page.name) for page in await self.pages.list_pages()]

    async def get_info(self, page: str | None = None) -> PageInfo:
        session = await self.pages.resolve(page)
        payload = await session.graph.get(session.id, {"fields": PAGE_FIELDS})
        return PageInfo.model_validate(payload)
