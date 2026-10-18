"""Shared building blocks for the service layer."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from facebook_mcp.domain import OperationResult
from facebook_mcp.pages import PageDirectory


@dataclass(frozen=True)
class PageAwareService:
    """A service that resolves the target Page (and its token) per call."""

    pages: PageDirectory


def fields(*names: str) -> str:
    return ",".join(names)


def operation_result(object_id: str, payload: dict[str, Any]) -> OperationResult:
    return OperationResult(id=object_id, success=bool(payload.get("success", False)))
