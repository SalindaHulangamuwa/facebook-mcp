from __future__ import annotations

from dataclasses import dataclass, field

from facebook_mcp.ports import GraphGateway


@dataclass(frozen=True)
class PageCredential:
    """A Page and the token that acts on it. The token is never shown in reprs."""

    id: str
    name: str | None
    access_token: str = field(repr=False)


@dataclass(frozen=True)
class PageSession:
    """A resolved Page plus a Graph gateway already authenticated for it."""

    id: str
    name: str | None
    graph: GraphGateway = field(repr=False)
