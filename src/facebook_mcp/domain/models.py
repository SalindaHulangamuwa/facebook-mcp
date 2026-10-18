"""Domain models returned by tools.

Graph API payloads are nested and inconsistent; these models flatten them
into stable, typed shapes so AI clients get predictable structured output.
`AliasPath` maps nested Graph fields without hand-written parsing code.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Generic, TypeVar

from pydantic import AliasPath, BaseModel, ConfigDict, Field, field_validator, model_validator

T = TypeVar("T", bound=BaseModel)


class GraphModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="ignore")


class PageSummary(GraphModel):
    id: str
    name: str | None = None


class PageInfo(GraphModel):
    id: str
    name: str
    category: str | None = None
    about: str | None = None
    link: str | None = None
    fan_count: int | None = None
    followers_count: int | None = None


class Post(GraphModel):
    id: str
    message: str | None = None
    created_time: str | None = None
    permalink_url: str | None = None
    full_picture: str | None = None
    is_published: bool | None = None
    share_count: int | None = Field(default=None, validation_alias=AliasPath("shares", "count"))
    reaction_count: int | None = Field(
        default=None, validation_alias=AliasPath("reactions", "summary", "total_count")
    )
    comment_count: int | None = Field(
        default=None, validation_alias=AliasPath("comments", "summary", "total_count")
    )


class Comment(GraphModel):
    id: str
    message: str | None = None
    created_time: str | None = None
    author_name: str | None = Field(default=None, validation_alias=AliasPath("from", "name"))
    like_count: int | None = None
    reply_count: int | None = Field(default=None, validation_alias="comment_count")
    is_hidden: bool | None = None


class InsightValue(GraphModel):
    value: Any
    end_time: str | None = None


class InsightMetric(GraphModel):
    name: str
    period: str
    title: str | None = None
    description: str | None = None
    values: list[InsightValue] = Field(default_factory=list)


class Paginated(GraphModel, Generic[T]):
    items: list[T]
    next_cursor: str | None = Field(
        default=None, description="Pass as `after` to fetch the next page; null when exhausted."
    )

    @classmethod
    def from_graph(cls, payload: dict[str, Any], item_model: type[T]) -> Paginated[T]:
        paging = payload.get("paging", {})
        has_next = "next" in paging
        return cls(
            items=[item_model.model_validate(item) for item in payload.get("data", [])],
            next_cursor=paging.get("cursors", {}).get("after") if has_next else None,
        )


class CreatedObject(GraphModel):
    """Result of a create call. Photo posts return both a photo id and a post id."""

    id: str
    post_id: str | None = None


class OperationResult(GraphModel):
    success: bool
    id: str


class PostDraft(GraphModel):
    """Validated input for publishing or scheduling a feed post."""

    message: str | None = None
    link: str | None = None
    scheduled_time: datetime | None = None

    @field_validator("scheduled_time")
    @classmethod
    def _must_be_future(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return None
        aware = value if value.tzinfo else value.replace(tzinfo=timezone.utc)
        if aware <= datetime.now(timezone.utc):
            raise ValueError("scheduled_time must be in the future")
        return aware

    @model_validator(mode="after")
    def _needs_content(self) -> PostDraft:
        if not (self.message or self.link):
            raise ValueError("A post needs a message, a link, or both.")
        return self

    def to_graph_params(self) -> dict[str, Any]:
        params: dict[str, Any] = {"message": self.message, "link": self.link}
        if self.scheduled_time:
            params |= {
                "published": "false",
                "scheduled_publish_time": int(self.scheduled_time.timestamp()),
            }
        return params
