from __future__ import annotations

from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import Any

import httpx
import pytest
from fastmcp import Client, FastMCP

from facebook_mcp.config import FacebookSettings
from facebook_mcp.server import build_server

PAGE_ID = "1000000000000001"
PAGE_TOKEN = "page-token-1"
OTHER_PAGE_ID = "1000000000000002"
OTHER_PAGE_TOKEN = "page-token-2"
USER_TOKEN = "user-token"


@dataclass
class FakeGraph:
    """Records requests and replies with canned responses keyed by (method, path)."""

    routes: dict[tuple[str, str], list[httpx.Response]] = field(default_factory=dict)
    requests: list[httpx.Request] = field(default_factory=list)

    def reply(self, method: str, path: str, json: Any, status: int = 200) -> None:
        self.reply_sequence(method, path, httpx.Response(status, json=json))

    def reply_sequence(self, method: str, path: str, *responses: httpx.Response) -> None:
        """Serve responses in order; the last one repeats for any further calls."""
        self.routes[(method, path)] = list(responses)

    def handler(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        path = request.url.path.split("/", 2)[-1]  # strip "/v26.0/"
        responses = self.routes.get((request.method, path))
        if not responses:
            return httpx.Response(404, json={"error": {"message": f"no route {path}", "code": 803}})
        return responses.pop(0) if len(responses) > 1 else responses[0]

    @property
    def transport(self) -> httpx.MockTransport:
        return httpx.MockTransport(self.handler)

    @property
    def last(self) -> httpx.Request:
        return self.requests[-1]

    def token_of(self, request: httpx.Request) -> str:
        return request.headers["Authorization"].removeprefix("Bearer ")


def single_page_settings(**overrides: Any) -> FacebookSettings:
    values: dict[str, Any] = {
        "FB_PAGE_ID": PAGE_ID,
        "FB_PAGE_ACCESS_TOKEN": PAGE_TOKEN,
        "FB_APP_SECRET": "app-secret",
        "_env_file": None,
    }
    return FacebookSettings(**(values | overrides))


def multi_page_settings(**overrides: Any) -> FacebookSettings:
    values: dict[str, Any] = {"FB_USER_ACCESS_TOKEN": USER_TOKEN, "_env_file": None}
    return FacebookSettings(**(values | overrides))


def stub_single_page(fake: FakeGraph) -> None:
    fake.reply("GET", PAGE_ID, {"id": PAGE_ID, "name": "Acme Bakery"})


def stub_accounts(fake: FakeGraph) -> None:
    fake.reply(
        "GET",
        "me/accounts",
        {
            "data": [
                {"id": PAGE_ID, "name": "Acme Bakery", "access_token": PAGE_TOKEN},
                {"id": OTHER_PAGE_ID, "name": "Acme Coffee", "access_token": OTHER_PAGE_TOKEN},
            ]
        },
    )


@pytest.fixture
def fake_graph() -> FakeGraph:
    fake = FakeGraph()
    stub_single_page(fake)
    return fake


@pytest.fixture
def server(fake_graph: FakeGraph) -> FastMCP:
    return build_server(single_page_settings(), http_transport=fake_graph.transport)


@pytest.fixture
async def client(server: FastMCP) -> AsyncIterator[Client]:
    async with Client(server) as connected:
        yield connected


@pytest.fixture
async def multi_client(fake_graph: FakeGraph) -> AsyncIterator[Client]:
    stub_accounts(fake_graph)
    server = build_server(multi_page_settings(), http_transport=fake_graph.transport)
    async with Client(server) as connected:
        yield connected
