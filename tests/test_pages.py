from __future__ import annotations

import httpx
import pytest
from fastmcp import Client
from fastmcp.exceptions import ToolError

from facebook_mcp.config import FacebookSettings
from facebook_mcp.graph import GraphClient
from facebook_mcp.pages import (
    AccountsPageSource,
    PageCredential,
    PageDirectory,
    PageNotFoundError,
    PageSelectionError,
)
from facebook_mcp.server import build_server
from tests.conftest import (
    OTHER_PAGE_ID,
    OTHER_PAGE_TOKEN,
    PAGE_ID,
    PAGE_TOKEN,
    USER_TOKEN,
    FakeGraph,
    multi_page_settings,
    stub_accounts,
)


class _ListSource:
    def __init__(self, *pages: PageCredential) -> None:
        self.pages = list(pages)
        self.loads = 0

    async def load(self) -> list[PageCredential]:
        self.loads += 1
        return self.pages


BAKERY = PageCredential(PAGE_ID, "Acme Bakery", PAGE_TOKEN)
COFFEE = PageCredential(OTHER_PAGE_ID, "Acme Coffee", OTHER_PAGE_TOKEN)


def _directory(*pages: PageCredential, default: str | None = None) -> PageDirectory:
    return PageDirectory(_ListSource(*pages), GraphClient(api_version="v26.0"), default)


async def test_single_page_is_used_implicitly() -> None:
    assert (await _directory(BAKERY).resolve()).id == PAGE_ID


@pytest.mark.parametrize("reference", [OTHER_PAGE_ID, "acme coffee", "ACME COFFEE"])
async def test_resolves_by_id_or_case_insensitive_name(reference: str) -> None:
    assert (await _directory(BAKERY, COFFEE).resolve(reference)).id == OTHER_PAGE_ID


async def test_infers_page_from_post_id() -> None:
    session = await _directory(BAKERY, COFFEE).resolve(object_id=f"{OTHER_PAGE_ID}_99")
    assert session.id == OTHER_PAGE_ID


async def test_uses_configured_default() -> None:
    assert (await _directory(BAKERY, COFFEE, default="Acme Coffee").resolve()).id == OTHER_PAGE_ID


async def test_requires_choice_when_several_pages() -> None:
    with pytest.raises(PageSelectionError, match="Acme Bakery"):
        await _directory(BAKERY, COFFEE).resolve()


async def test_unknown_page_lists_alternatives() -> None:
    with pytest.raises(PageNotFoundError, match=r"Acme Coffee \[" + OTHER_PAGE_ID):
        await _directory(BAKERY, COFFEE).resolve("nope")


async def test_pages_load_once_until_invalidated() -> None:
    source = _ListSource(BAKERY)
    directory = PageDirectory(source, GraphClient(api_version="v26.0"))

    await directory.resolve()
    await directory.list_pages()
    directory.invalidate()
    await directory.resolve()

    assert source.loads == 2


async def test_accounts_source_follows_pagination(fake_graph: FakeGraph) -> None:
    fake_graph.reply_sequence(
        "GET",
        "me/accounts",
        httpx.Response(
            200,
            json={
                "data": [{"id": PAGE_ID, "name": "A", "access_token": PAGE_TOKEN}],
                "paging": {"cursors": {"after": "NEXT"}, "next": "https://next"},
            },
        ),
        httpx.Response(
            200,
            json={"data": [{"id": OTHER_PAGE_ID, "name": "B", "access_token": OTHER_PAGE_TOKEN}]},
        ),
    )
    graph = GraphClient(api_version="v26.0", transport=fake_graph.transport)

    credentials = await AccountsPageSource(graph, USER_TOKEN).load()

    assert [c.id for c in credentials] == [PAGE_ID, OTHER_PAGE_ID]
    assert fake_graph.last.url.params["after"] == "NEXT"
    assert fake_graph.token_of(fake_graph.last) == USER_TOKEN


async def test_list_pages_tool(multi_client: Client) -> None:
    result = await multi_client.call_tool("list_pages", {})

    names = [page["name"] for page in result.structured_content["result"]]
    assert names == ["Acme Bakery", "Acme Coffee"]


async def test_tools_use_the_selected_pages_token(
    multi_client: Client, fake_graph: FakeGraph
) -> None:
    fake_graph.reply("GET", f"{OTHER_PAGE_ID}/posts", {"data": []})

    await multi_client.call_tool("list_posts", {"page": "Acme Coffee"})

    assert fake_graph.token_of(fake_graph.last) == OTHER_PAGE_TOKEN


async def test_missing_page_choice_is_reported_to_client(multi_client: Client) -> None:
    with pytest.raises(ToolError, match="Several Pages are available"):
        await multi_client.call_tool("get_page_info", {})


async def test_default_page_setting_applies(fake_graph: FakeGraph) -> None:
    stub_accounts(fake_graph)
    server = build_server(
        multi_page_settings(FB_DEFAULT_PAGE=OTHER_PAGE_ID), http_transport=fake_graph.transport
    )
    fake_graph.reply("GET", OTHER_PAGE_ID, {"id": OTHER_PAGE_ID, "name": "Acme Coffee"})

    async with Client(server) as client:
        result = await client.call_tool("get_page_info", {})

    assert result.structured_content["id"] == OTHER_PAGE_ID


@pytest.mark.parametrize(
    ("env", "message"),
    [
        ({}, "No Facebook credentials"),
        ({"FB_PAGE_ID": PAGE_ID}, "No Facebook credentials"),
        (
            {"FB_USER_ACCESS_TOKEN": USER_TOKEN, "FB_PAGE_ID": PAGE_ID},
            "not both",
        ),
    ],
)
def test_settings_require_exactly_one_credential_mode(env: dict[str, str], message: str) -> None:
    with pytest.raises(ValueError, match=message):
        FacebookSettings(**env, _env_file=None)  # type: ignore[arg-type]
