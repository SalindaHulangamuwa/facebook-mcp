from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any
from urllib.parse import parse_qs

import httpx
import pytest
from fastmcp import Client
from fastmcp.exceptions import ToolError

from facebook_mcp.server import build_server
from tests.conftest import PAGE_ID, PAGE_TOKEN, FakeGraph, single_page_settings

POST_ID = f"{PAGE_ID}_42"


def _form(fake: FakeGraph) -> dict[str, str]:
    return {key: values[0] for key, values in parse_qs(fake.last.content.decode()).items()}


async def test_get_page_info(client: Client, fake_graph: FakeGraph) -> None:
    fake_graph.reply("GET", PAGE_ID, {"id": PAGE_ID, "name": "Acme Bakery", "fan_count": 10})

    result = await client.call_tool("get_page_info", {})

    assert fake_graph.token_of(fake_graph.last) == PAGE_TOKEN
    assert result.structured_content["name"] == "Acme Bakery"
    assert result.structured_content["fan_count"] == 10


async def test_list_posts_flattens_engagement_and_cursor(
    client: Client, fake_graph: FakeGraph
) -> None:
    fake_graph.reply(
        "GET",
        f"{PAGE_ID}/posts",
        {
            "data": [
                {
                    "id": POST_ID,
                    "message": "hello",
                    "reactions": {"data": [], "summary": {"total_count": 7}},
                    "comments": {"data": [], "summary": {"total_count": 2}},
                }
            ],
            "paging": {"cursors": {"after": "CUR"}, "next": "https://next"},
        },
    )

    result = await client.call_tool("list_posts", {"limit": 5})

    page = result.structured_content
    assert page["next_cursor"] == "CUR"
    assert page["items"][0]["reaction_count"] == 7
    assert page["items"][0]["comment_count"] == 2
    assert fake_graph.last.url.params["limit"] == "5"


async def test_last_page_has_no_cursor(client: Client, fake_graph: FakeGraph) -> None:
    fake_graph.reply("GET", f"{PAGE_ID}/posts", {"data": [], "paging": {"cursors": {"after": "X"}}})

    result = await client.call_tool("list_posts", {})

    assert result.structured_content["next_cursor"] is None


async def test_create_scheduled_post(client: Client, fake_graph: FakeGraph) -> None:
    fake_graph.reply("POST", f"{PAGE_ID}/feed", {"id": POST_ID})
    when = datetime.now(timezone.utc) + timedelta(days=1)

    result = await client.call_tool(
        "create_post", {"message": "launch!", "scheduled_time": when.isoformat()}
    )

    assert result.structured_content["id"] == POST_ID
    form = _form(fake_graph)
    assert form["published"] == "false"
    assert form["scheduled_publish_time"] == str(int(when.timestamp()))


async def test_create_post_requires_content(client: Client) -> None:
    with pytest.raises(ToolError, match="message, a link, or both"):
        await client.call_tool("create_post", {})


async def test_rejects_malformed_ids(client: Client) -> None:
    with pytest.raises(ToolError):
        await client.call_tool("delete_post", {"post_id": "../me"})


async def test_hide_comment(client: Client, fake_graph: FakeGraph) -> None:
    fake_graph.reply("POST", "555", {"success": True})

    result = await client.call_tool("set_comment_hidden", {"comment_id": "555"})

    assert result.structured_content == {"success": True, "id": "555"}
    assert _form(fake_graph) == {"is_hidden": "true"}


async def test_graph_errors_reach_client_with_hint(client: Client, fake_graph: FakeGraph) -> None:
    fake_graph.reply(
        "GET", PAGE_ID, {"error": {"message": "Session expired", "code": 190}}, status=401
    )  # fails the Page-name lookup too, exactly like an expired token would

    with pytest.raises(ToolError, match="Generate a new Page access token"):
        await client.call_tool("get_page_info", {})


async def test_post_insights_uses_defaults(client: Client, fake_graph: FakeGraph) -> None:
    fake_graph.reply(
        "GET",
        f"{POST_ID}/insights",
        {"data": [{"name": "post_clicks", "period": "lifetime", "values": [{"value": 3}]}]},
    )

    result = await client.call_tool("get_post_insights", {"post_id": POST_ID})

    assert result.structured_content["result"][0]["values"][0]["value"] == 3
    assert fake_graph.last.url.params["metric"] == "post_reactions_by_type_total,post_clicks"


async def test_read_only_mode_hides_write_tools(fake_graph: FakeGraph) -> None:
    server = build_server(
        single_page_settings(), read_only=True, http_transport=fake_graph.transport
    )

    async with Client(server) as client:
        names = {tool.name for tool in await client.list_tools()}

    assert "get_page_info" in names
    assert names.isdisjoint({"create_post", "delete_post", "add_comment", "delete_comment"})


async def test_all_tools_carry_annotations(client: Client) -> None:
    tools = await client.list_tools()

    assert len(tools) == 16
    assert all(tool.annotations is not None for tool in tools)
    page_aware = [tool for tool in tools if tool.name != "list_pages"]
    assert all("page" in tool.input_schema["properties"] for tool in page_aware)


COMMENT_ID = "42_7"


@dataclass(frozen=True)
class Route:
    """A tool call and the single Graph request it should produce."""

    tool: str
    arguments: dict[str, Any]
    method: str
    path: str
    response: dict[str, Any] = field(default_factory=lambda: {"success": True})


ROUTES = [
    Route("list_scheduled_posts", {}, "GET", f"{PAGE_ID}/scheduled_posts", {"data": []}),
    Route("get_post", {"post_id": POST_ID}, "GET", POST_ID, {"id": POST_ID}),
    Route(
        "create_photo_post",
        {"image_url": "https://example.com/cat.jpg", "caption": "cat"},
        "POST",
        f"{PAGE_ID}/photos",
        {"id": "9", "post_id": POST_ID},
    ),
    Route("update_post", {"post_id": POST_ID, "message": "edit"}, "POST", POST_ID),
    Route("delete_post", {"post_id": POST_ID}, "DELETE", POST_ID),
    Route("list_comments", {"object_id": POST_ID}, "GET", f"{POST_ID}/comments", {"data": []}),
    Route(
        "add_comment",
        {"object_id": POST_ID, "message": "thanks!"},
        "POST",
        f"{POST_ID}/comments",
        {"id": COMMENT_ID},
    ),
    Route("delete_comment", {"comment_id": COMMENT_ID}, "DELETE", COMMENT_ID),
    Route("get_page_insights", {"period": "week"}, "GET", f"{PAGE_ID}/insights", {"data": []}),
]


@pytest.mark.parametrize("route", ROUTES, ids=[route.tool for route in ROUTES])
async def test_tools_call_the_expected_graph_endpoint(
    client: Client, fake_graph: FakeGraph, route: Route
) -> None:
    fake_graph.reply(route.method, route.path, route.response)

    result = await client.call_tool(route.tool, route.arguments)

    assert not result.is_error
    assert (fake_graph.last.method, fake_graph.last.url.path) == (
        route.method,
        f"/v26.0/{route.path}",
    )
    assert fake_graph.token_of(fake_graph.last) == PAGE_TOKEN


async def test_create_reel_uploads_then_schedules(
    client: Client, fake_graph: FakeGraph, tmp_path: Any
) -> None:
    video = tmp_path / "reel.mp4"
    video.write_bytes(b"\x00\x00\x00\x18ftypmp42")
    upload_url = "https://rupload.facebook.com/video-upload/v26.0/777"
    fake_graph.reply_sequence(
        "POST",
        f"{PAGE_ID}/video_reels",
        httpx.Response(200, json={"video_id": "777", "upload_url": upload_url}),
        httpx.Response(200, json={"success": True}),
    )
    fake_graph.reply("POST", "v26.0/777", {"success": True})

    result = await client.call_tool(
        "create_reel",
        {
            "video_path": str(video),
            "description": "How Bluetooth works",
            "scheduled_time": "2999-01-01T00:00:00Z",
        },
    )

    assert not result.is_error
    start, upload, finish = fake_graph.requests[-3:]
    assert b"upload_phase=start" in start.content
    assert upload.url.host == "rupload.facebook.com"
    assert upload.headers["Authorization"] == f"OAuth {PAGE_TOKEN}"
    assert upload.headers["file_size"] == str(len(video.read_bytes()))
    assert b"video_state=SCHEDULED" in finish.content
    assert b"video_id=777" in finish.content


async def test_create_reel_rejects_missing_file(client: Client) -> None:
    with pytest.raises(ToolError, match="video file not found"):
        await client.call_tool("create_reel", {"video_path": "/nope/missing.mp4"})
