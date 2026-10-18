from __future__ import annotations

from fastmcp import FastMCP

from facebook_mcp.domain import Comment, CreatedObject, OperationResult, Paginated
from facebook_mcp.services import CommentService
from facebook_mcp.services.comments import CommentOrder
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


def register(mcp: FastMCP, comments: CommentService) -> None:
    @tool(mcp, annotations=READ_ONLY)
    async def list_comments(
        object_id: GraphId,
        limit: Limit = 25,
        after: Cursor = None,
        order: CommentOrder = "reverse_chronological",
        page: PageRef = None,
    ) -> Paginated[Comment]:
        """List comments on a post, or replies to a comment."""
        return await comments.list_comments(object_id, limit, after, order, page)

    @tool(mcp, annotations=CREATES, tags={WRITE_TAG})
    async def add_comment(
        object_id: GraphId, message: Message, page: PageRef = None
    ) -> CreatedObject:
        """Comment as the Page on a post, or reply to a comment by passing its id."""
        return await comments.add_comment(object_id, message, page)

    @tool(mcp, annotations=MODIFIES, tags={WRITE_TAG})
    async def set_comment_hidden(
        comment_id: GraphId, hidden: bool = True, page: PageRef = None
    ) -> OperationResult:
        """Hide (or unhide) a comment. Hidden comments stay visible only to their author."""
        return await comments.set_hidden(comment_id, hidden, page)

    @tool(mcp, annotations=MODIFIES, tags={WRITE_TAG})
    async def delete_comment(comment_id: GraphId, page: PageRef = None) -> OperationResult:
        """Permanently delete a comment. This cannot be undone."""
        return await comments.delete_comment(comment_id, page)
