"""The Graph API port the rest of the application depends on.

Kept in its own dependency-free module so both the `pages` and `services`
packages can rely on the abstraction without importing each other.
"""

from __future__ import annotations

from typing import Any, Protocol


class GraphGateway(Protocol):
    """Token-bound access to the Graph API (implemented by `graph.BoundGraph`)."""

    async def get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]: ...

    async def post(self, path: str, data: dict[str, Any] | None = None) -> dict[str, Any]: ...

    async def delete(self, path: str) -> dict[str, Any]: ...
