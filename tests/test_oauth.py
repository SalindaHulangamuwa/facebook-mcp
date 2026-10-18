from __future__ import annotations

from facebook_mcp.graph import GraphClient
from facebook_mcp.oauth import exchange_for_long_lived_token
from tests.conftest import FakeGraph


async def test_exchanges_short_lived_token(fake_graph: FakeGraph) -> None:
    fake_graph.reply("GET", "oauth/access_token", {"access_token": "long-lived"})
    graph = GraphClient(api_version="v26.0", transport=fake_graph.transport)

    token = await exchange_for_long_lived_token(
        graph, app_id="123", app_secret="shh", short_lived_token="short"
    )

    params = fake_graph.last.url.params
    assert token == "long-lived"
    assert params["grant_type"] == "fb_exchange_token"
    assert params["fb_exchange_token"] == "short"
