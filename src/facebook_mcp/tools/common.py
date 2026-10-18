"""Reusable parameter types, tags and annotations shared by every tool module."""

from __future__ import annotations

from collections.abc import Callable
from typing import Annotated, Any, TypeVar

from fastmcp import FastMCP
from mcp.types import ToolAnnotations
from pydantic import Field

from facebook_mcp.tools.errors import translate_errors

F = TypeVar("F", bound=Callable[..., Any])

WRITE_TAG = "write"

READ_ONLY = ToolAnnotations(read_only_hint=True, idempotent_hint=True, open_world_hint=True)
CREATES = ToolAnnotations(read_only_hint=False, destructive_hint=False, open_world_hint=True)
MODIFIES = ToolAnnotations(
    read_only_hint=False, destructive_hint=True, idempotent_hint=True, open_world_hint=True
)

GraphId = Annotated[
    str,
    Field(
        min_length=1,
        pattern=r"^\d+(_\d+)?$",
        description="Graph object id, e.g. '1234567890' or '<pageid>_<postid>'.",
    ),
]
Limit = Annotated[int, Field(ge=1, le=100, description="Maximum number of items to return.")]
Cursor = Annotated[
    str | None,
    Field(description="`next_cursor` from a previous call to fetch the next page."),
]
PageRef = Annotated[
    str | None,
    Field(
        description=(
            "Page id or exact Page name. Omit to use the default Page "
            "(or the Page that owns the given post)."
        )
    ),
]
Message = Annotated[str, Field(min_length=1, max_length=63206, description="Text content.")]


def tool(mcp: FastMCP, **options: Any) -> Callable[[F], F]:
    """Register a tool on `mcp` with uniform error translation applied."""

    def decorator(fn: F) -> F:
        mcp.tool(translate_errors(fn), **options)
        return fn

    return decorator
