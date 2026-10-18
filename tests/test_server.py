from __future__ import annotations

import pytest
from fastmcp import Client, FastMCP

from facebook_mcp.auth import StaticBearerTokenVerifier
from facebook_mcp.cli import auth_for, main, parse_args, resolve_server_settings
from tests.conftest import PAGE_ID, FakeGraph


async def test_server_survives_multiple_sessions(server: FastMCP, fake_graph: FakeGraph) -> None:
    for _ in range(2):
        async with Client(server) as client:
            result = await client.call_tool("get_page_info", {})
            assert result.structured_content["id"] == PAGE_ID


async def test_bearer_verifier_accepts_only_expected_token() -> None:
    verifier = StaticBearerTokenVerifier("s3cret")

    assert await verifier.verify_token("s3cret") is not None
    assert await verifier.verify_token("wrong") is None


def test_serve_is_the_default_command() -> None:
    assert parse_args([]).command == "serve"
    assert parse_args(["--transport", "http"]).transport == "http"


def test_auth_only_applies_to_http(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MCP_AUTH_TOKEN", "tok")

    stdio = resolve_server_settings(parse_args(["--transport", "stdio"]))
    http = resolve_server_settings(parse_args(["serve", "--transport", "http", "--port", "9000"]))

    assert auth_for(stdio) is None
    assert isinstance(auth_for(http), StaticBearerTokenVerifier)
    assert http.port == 9000


def test_missing_credentials_exit_with_clear_message(
    monkeypatch: pytest.MonkeyPatch, tmp_path, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(tmp_path)  # no .env here
    for name in ("FB_USER_ACCESS_TOKEN", "FB_PAGE_ID", "FB_PAGE_ACCESS_TOKEN"):
        monkeypatch.delenv(name, raising=False)

    with pytest.raises(SystemExit) as exit_info:
        main([])

    assert exit_info.value.code == 2
    assert "No Facebook credentials" in capsys.readouterr().err
