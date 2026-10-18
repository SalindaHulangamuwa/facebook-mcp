"""Command-line interface.

    facebook-mcp [serve] [--transport stdio|http] [--host H] [--port P] [--read-only]
    facebook-mcp exchange-token --app-id ID --app-secret SECRET --token SHORT_LIVED_TOKEN

`serve` is the default command, so MCP client configs can simply run `facebook-mcp`.
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import os
import sys
from collections.abc import Callable, Sequence
from typing import Any, get_args

from pydantic import ValidationError

from facebook_mcp import __version__
from facebook_mcp.auth import StaticBearerTokenVerifier
from facebook_mcp.config import FacebookSettings, ServerSettings, TransportName
from facebook_mcp.exceptions import FacebookMCPError
from facebook_mcp.graph import GraphClient
from facebook_mcp.oauth import exchange_for_long_lived_token
from facebook_mcp.server import build_server

COMMANDS = ("serve", "exchange-token")
EXIT_CONFIG_ERROR = 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="facebook-mcp", description="Facebook Pages MCP server")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    commands = parser.add_subparsers(dest="command", required=True)

    serve = commands.add_parser("serve", help="Run the MCP server (default).")
    serve.add_argument("--transport", choices=get_args(TransportName))
    serve.add_argument("--host")
    serve.add_argument("--port", type=int)
    serve.add_argument("--read-only", action="store_true", default=None)
    serve.set_defaults(handler=serve_command)

    exchange = commands.add_parser(
        "exchange-token", help="Turn a short-lived user token into a long-lived one."
    )
    exchange.add_argument("--app-id", required=True)
    env_secret = os.environ.get("FB_APP_SECRET")
    exchange.add_argument(
        "--app-secret",
        default=env_secret,
        required=env_secret is None,
        help="Defaults to $FB_APP_SECRET (keeps the secret out of shell history).",
    )
    exchange.add_argument("--token", required=True, help="Short-lived user access token.")
    exchange.add_argument("--api-version", default="v26.0")
    exchange.set_defaults(handler=exchange_token_command)
    return parser


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    args = list(sys.argv[1:] if argv is None else argv)
    if not args or args[0] not in (*COMMANDS, "-h", "--help", "--version"):
        args.insert(0, "serve")
    return build_parser().parse_args(args)


def resolve_server_settings(args: argparse.Namespace) -> ServerSettings:
    """CLI flags override environment variables, which override defaults."""
    flags = ("transport", "host", "port", "read_only")
    overrides = {name: getattr(args, name) for name in flags if getattr(args, name) is not None}
    return ServerSettings(**overrides)


def auth_for(server: ServerSettings) -> StaticBearerTokenVerifier | None:
    if server.transport == "stdio" or server.auth_token is None:
        return None
    return StaticBearerTokenVerifier(server.auth_token.get_secret_value())


def transport_options(server: ServerSettings) -> dict[str, Any]:
    if server.transport == "stdio":
        return {}
    return {"host": server.host, "port": server.port, "path": server.path}


def serve_command(args: argparse.Namespace) -> None:
    server_settings = resolve_server_settings(args)
    # Logs must go to stderr: stdout is the MCP channel in stdio mode.
    logging.basicConfig(stream=sys.stderr, level=server_settings.log_level.upper())
    mcp = build_server(
        FacebookSettings(), read_only=server_settings.read_only, auth=auth_for(server_settings)
    )
    mcp.run(
        transport=server_settings.transport,
        show_banner=False,
        **transport_options(server_settings),
    )


def exchange_token_command(args: argparse.Namespace) -> None:
    async def run() -> str:
        async with GraphClient(api_version=args.api_version) as graph:
            return await exchange_for_long_lived_token(
                graph, app_id=args.app_id, app_secret=args.app_secret, short_lived_token=args.token
            )

    sys.stdout.write(f"{asyncio.run(run())}\n")


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    handler: Callable[[argparse.Namespace], None] = args.handler
    try:
        handler(args)
    except ValidationError as exc:
        _fail(f"Invalid configuration:\n{_format_validation_error(exc)}")
    except FacebookMCPError as exc:
        _fail(exc.user_message)


def _format_validation_error(exc: ValidationError) -> str:
    return "\n".join(f"  - {error['msg'].removeprefix('Value error, ')}" for error in exc.errors())


def _fail(message: str) -> None:
    sys.stderr.write(f"facebook-mcp: {message}\n")
    raise SystemExit(EXIT_CONFIG_ERROR)
