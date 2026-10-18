from __future__ import annotations

from facebook_mcp.domain import CreatedObject, OperationResult, Paginated, Post, PostDraft
from facebook_mcp.pages import PageSession
from facebook_mcp.services.base import PageAwareService, fields, operation_result

POST_FIELDS = fields(
    "id",
    "message",
    "created_time",
    "permalink_url",
    "full_picture",
    "is_published",
    "shares",
    "reactions.summary(total_count).limit(0)",
    "comments.summary(total_count).limit(0)",
)


class PostService(PageAwareService):
    async def list_posts(
        self, limit: int, after: str | None = None, page: str | None = None
    ) -> Paginated[Post]:
        return await self._list(await self.pages.resolve(page), "posts", limit, after)

    async def list_scheduled_posts(
        self, limit: int, after: str | None = None, page: str | None = None
    ) -> Paginated[Post]:
        return await self._list(await self.pages.resolve(page), "scheduled_posts", limit, after)

    async def get_post(self, post_id: str, page: str | None = None) -> Post:
        session = await self.pages.resolve(page, object_id=post_id)
        return Post.model_validate(await session.graph.get(post_id, {"fields": POST_FIELDS}))

    async def create_post(self, draft: PostDraft, page: str | None = None) -> CreatedObject:
        session = await self.pages.resolve(page)
        payload = await session.graph.post(f"{session.id}/feed", draft.to_graph_params())
        return CreatedObject.model_validate(payload)

    async def create_photo_post(
        self, image_url: str, caption: str | None = None, page: str | None = None
    ) -> CreatedObject:
        session = await self.pages.resolve(page)
        payload = await session.graph.post(
            f"{session.id}/photos", {"url": image_url, "caption": caption}
        )
        return CreatedObject.model_validate(payload)

    async def update_post(
        self, post_id: str, message: str, page: str | None = None
    ) -> OperationResult:
        session = await self.pages.resolve(page, object_id=post_id)
        return operation_result(post_id, await session.graph.post(post_id, {"message": message}))

    async def delete_post(self, post_id: str, page: str | None = None) -> OperationResult:
        session = await self.pages.resolve(page, object_id=post_id)
        return operation_result(post_id, await session.graph.delete(post_id))

    @staticmethod
    async def _list(
        session: PageSession, edge: str, limit: int, after: str | None
    ) -> Paginated[Post]:
        payload = await session.graph.get(
            f"{session.id}/{edge}", {"fields": POST_FIELDS, "limit": limit, "after": after}
        )
        return Paginated[Post].from_graph(payload, Post)
