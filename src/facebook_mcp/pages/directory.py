"""Resolves "which Page?" for every tool call.

Resolution order for a call:
1. the explicit `page` argument (an id, or a case-insensitive name);
2. the Page that owns the object, inferred from a `<pageid>_<postid>` id;
3. the configured default Page (`FB_DEFAULT_PAGE`);
4. the only available Page, when there is exactly one.
"""

from __future__ import annotations

import asyncio
from collections.abc import Iterable

from facebook_mcp.graph import GraphClient
from facebook_mcp.pages.errors import PageNotFoundError, PageSelectionError
from facebook_mcp.pages.models import PageCredential, PageSession
from facebook_mcp.pages.sources import PageSource

PageIndex = dict[str, PageCredential]


class PageDirectory:
    def __init__(
        self, source: PageSource, graph: GraphClient, default_page: str | None = None
    ) -> None:
        self._source = source
        self._graph = graph
        self._default_page = default_page
        self._index: PageIndex | None = None
        self._lock = asyncio.Lock()

    async def list_pages(self) -> list[PageCredential]:
        return list((await self._load()).values())

    async def resolve(
        self, page: str | None = None, *, object_id: str | None = None
    ) -> PageSession:
        index = await self._load()
        reference = page or _owning_page_id(object_id, index) or self._default_page
        credential = _find(index, reference) if reference else _only_page(index)
        return PageSession(
            credential.id, credential.name, self._graph.bind(credential.access_token)
        )

    def invalidate(self) -> None:
        """Forget discovered Pages so the next call reloads them (e.g. after a token change)."""
        self._index = None

    async def _load(self) -> PageIndex:
        async with self._lock:
            if self._index is None:
                self._index = {page.id: page for page in await self._source.load()}
            return self._index


def _owning_page_id(object_id: str | None, index: PageIndex) -> str | None:
    prefix, separator, _ = (object_id or "").partition("_")
    return prefix if separator and prefix in index else None


def _find(index: PageIndex, reference: str) -> PageCredential:
    if reference in index:
        return index[reference]
    matches = [
        page for page in index.values() if (page.name or "").casefold() == reference.casefold()
    ]
    if len(matches) == 1:
        return matches[0]
    if matches:
        raise PageSelectionError(
            f"Several Pages are named '{reference}'. Use the Page id: {_describe(matches)}"
        )
    raise PageNotFoundError(
        f"No Page matches '{reference}'. Available Pages: {_describe(index.values())}"
    )


def _only_page(index: PageIndex) -> PageCredential:
    if len(index) == 1:
        return next(iter(index.values()))
    if not index:
        raise PageNotFoundError("The configured token cannot manage any Facebook Page.")
    raise PageSelectionError(
        "Several Pages are available. Pass `page` (id or name), or set FB_DEFAULT_PAGE. "
        f"Available Pages: {_describe(index.values())}"
    )


def _describe(pages: Iterable[PageCredential]) -> str:
    return ", ".join(f"{page.name or '(unnamed)'} [{page.id}]" for page in pages)
