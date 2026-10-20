from __future__ import annotations

import hashlib
import hmac

import httpx
import pytest

from facebook_mcp.graph import (
    GraphAuthError,
    GraphClient,
    GraphConnectionError,
    GraphPermissionError,
    GraphRateLimitError,
    GraphTimeoutError,
)
from facebook_mcp.graph.client import compute_appsecret_proof
from tests.conftest import FakeGraph


def _client(fake: FakeGraph, app_secret: str | None = "secret") -> GraphClient:
    return GraphClient(api_version="v26.0", app_secret=app_secret, transport=fake.transport)


def test_appsecret_proof_matches_meta_spec() -> None:
    expected = hmac.new(b"secret", b"token", hashlib.sha256).hexdigest()
    assert compute_appsecret_proof("token", "secret") == expected


async def test_bound_graph_sends_bearer_token_and_proof(fake_graph: FakeGraph) -> None:
    fake_graph.reply("GET", "me", {"id": "1"})

    await _client(fake_graph).bind("token").get("me", {"fields": "id", "after": None})

    request = fake_graph.last
    assert request.headers["Authorization"] == "Bearer token"
    assert request.url.params["appsecret_proof"] == compute_appsecret_proof("token", "secret")
    assert "after" not in request.url.params
    assert "access_token" not in request.url.params


async def test_omits_proof_without_app_secret(fake_graph: FakeGraph) -> None:
    fake_graph.reply("GET", "me", {"id": "1"})

    await _client(fake_graph, app_secret=None).bind("token").get("me")

    assert "appsecret_proof" not in fake_graph.last.url.params


async def test_unauthenticated_request_sends_no_credentials(fake_graph: FakeGraph) -> None:
    fake_graph.reply("GET", "oauth/access_token", {"access_token": "long"})

    await _client(fake_graph).request("GET", "oauth/access_token")

    assert "Authorization" not in fake_graph.last.headers
    assert "appsecret_proof" not in fake_graph.last.url.params


def test_bound_graph_repr_hides_token() -> None:
    assert "secret-token" not in repr(GraphClient(api_version="v26.0").bind("secret-token"))


@pytest.mark.parametrize(
    ("code", "error_type"),
    [(190, GraphAuthError), (200, GraphPermissionError), (4, GraphRateLimitError)],
)
async def test_maps_error_codes(fake_graph: FakeGraph, code: int, error_type: type) -> None:
    fake_graph.reply("GET", "me", {"error": {"message": "nope", "code": code}}, status=400)

    with pytest.raises(error_type) as caught:
        await _client(fake_graph).bind("token").get("me")

    assert caught.value.code == code
    assert caught.value.hint in caught.value.user_message


async def test_wraps_network_failures() -> None:
    def explode(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("boom", request=request)

    client = GraphClient(api_version="v26.0", transport=httpx.MockTransport(explode))
    with pytest.raises(GraphConnectionError):
        await client.bind("t").get("me")


async def test_timeouts_raise_actionable_error() -> None:
    def stall(request: httpx.Request) -> httpx.Response:
        raise httpx.WriteTimeout("timed out", request=request)

    client = GraphClient(api_version="v26.0", transport=httpx.MockTransport(stall))
    with pytest.raises(GraphTimeoutError) as caught:
        await client.bind("t").upload("https://rupload.facebook.com/x", b"data", {})

    assert "FB_UPLOAD_TIMEOUT" in caught.value.user_message


async def test_uploads_use_the_long_upload_timeout(fake_graph: FakeGraph) -> None:
    fake_graph.reply("POST", "x", {"success": True})
    client = GraphClient(
        api_version="v26.0", timeout=30, upload_timeout=600, transport=fake_graph.transport
    )

    await client.bind("t").upload("https://rupload.facebook.com/v26.0/x", b"data", {})

    timeout = fake_graph.last.extensions["timeout"]
    assert (timeout["connect"], timeout["write"], timeout["read"]) == (30, 600, 600)
