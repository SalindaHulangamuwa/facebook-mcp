from __future__ import annotations

from typing import Literal

from facebook_mcp.domain import Comment, CreatedObject, OperationResult, Paginated
from facebook_mcp.services.base import PageAwareService, fields, operation_result

CommentOrder = Literal["chronological", "reverse_chronological"]

COMMENT_FIELDS = fields(
    "id", "message", "created_time", "from", "like_count", "comment_count", "is_hidden"
)


class CommentService(PageAwareService):
    async def list_comments(
        self,
        object_id: str,
        limit: int,
        after: str | None = None,
        order: CommentOrder = "reverse_chronological",
        page: str | None = None,
    ) -> Paginated[Comment]:
        session = await self.pages.resolve(page, object_id=object_id)
        payload = await session.graph.get(
            f"{object_id}/comments",
            {"fields": COMMENT_FIELDS, "limit": limit, "after": after, "order": order},
        )
        return Paginated[Comment].from_graph(payload, Comment)

    async def add_comment(
        self, object_id: str, message: str, page: str | None = None
    ) -> CreatedObject:
        """Comment on a post, or reply to a comment when `object_id` is a comment id."""
        session = await self.pages.resolve(page, object_id=object_id)
        payload = await session.graph.post(f"{object_id}/comments", {"message": message})
        return CreatedObject.model_validate(payload)

    async def set_hidden(
        self, comment_id: str, hidden: bool, page: str | None = None
    ) -> OperationResult:
        session = await self.pages.resolve(page, object_id=comment_id)
        payload = await session.graph.post(comment_id, {"is_hidden": str(hidden).lower()})
        return operation_result(comment_id, payload)

    async def delete_comment(self, comment_id: str, page: str | None = None) -> OperationResult:
        session = await self.pages.resolve(page, object_id=comment_id)
        return operation_result(comment_id, await session.graph.delete(comment_id))
