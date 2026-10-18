"""Strategies for discovering which Pages the server may act on."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from pydantic import BaseModel, SecretStr

from facebook_mcp.config import FacebookSettings
from facebook_mcp.domain import Paginated
from facebook_mcp.graph import GraphClient
from facebook_mcp.pages.models import PageCredential

ACCOUNTS_PAGE_SIZE = 100


class PageSource(Protocol):
    async def load(self) -> list[PageCredential]: ...


@dataclass(frozen=True)
class StaticPageSource:
    """One Page configured explicitly. Its name is looked up once, on first use."""

    graph: GraphClient
    page_id: str
    access_token: str = field(repr=False)

    async def load(self) -> list[PageCredential]:
        page = await self.graph.bind(self.access_token).get(self.page_id, {"fields": "name"})
        return [PageCredential(self.page_id, page.get("name"), self.access_token)]


class _AccountEntry(BaseModel):
    id: str
    name: str | None = None
    access_token: SecretStr


@dataclass(frozen=True)
class AccountsPageSource:
    """Every Page the user manages, discovered via `/me/accounts` (paginated)."""

    graph: GraphClient
    user_access_token: str = field(repr=False)

    async def load(self) -> list[PageCredential]:
        entries: list[_AccountEntry] = []
        cursor: str | None = None
        while True:
            batch = await self._fetch(cursor)
            entries.extend(batch.items)
            if batch.next_cursor is None:
                return [_to_credential(entry) for entry in entries]
            cursor = batch.next_cursor

    async def _fetch(self, cursor: str | None) -> Paginated[_AccountEntry]:
        payload = await self.graph.bind(self.user_access_token).get(
            "me/accounts",
            {"fields": "id,name,access_token", "limit": ACCOUNTS_PAGE_SIZE, "after": cursor},
        )
        return Paginated[_AccountEntry].from_graph(payload, _AccountEntry)


def _to_credential(entry: _AccountEntry) -> PageCredential:
    return PageCredential(entry.id, entry.name, entry.access_token.get_secret_value())


def page_source_from_settings(settings: FacebookSettings, graph: GraphClient) -> PageSource:
    if settings.user_access_token:
        return AccountsPageSource(graph, settings.user_access_token.get_secret_value())
    page_id, token = settings.single_page_credentials()
    return StaticPageSource(graph, page_id, token)
