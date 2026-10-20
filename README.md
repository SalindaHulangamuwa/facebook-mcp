# facebook-mcp

[![CI](https://github.com/SalindaHulangamuwa/facebook-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/SalindaHulangamuwa/facebook-mcp/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/facebook-mcp.svg)](https://pypi.org/project/facebook-mcp/)
[![Python](https://img.shields.io/pypi/pyversions/facebook-mcp.svg)](https://pypi.org/project/facebook-mcp/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

<!-- mcp-name: io.github.SalindaHulangamuwa/facebook-mcp -->

An open-source [Model Context Protocol](https://modelcontextprotocol.io) server that
lets AI assistants manage your **Facebook Pages**: publish and schedule posts,
moderate comments, and read analytics. It's built on [FastMCP](https://gofastmcp.com)
and works with Claude Desktop, Claude Code, ChatGPT, Gemini CLI, Cursor, VS Code
and any other MCP client.

> "Schedule tomorrow's 9am post on Acme Coffee announcing the new menu, then hide
> any spam comments on yesterday's post."

## Features

- **Multi-page:** give it one user token and it finds every Page you manage.
  Each Page uses its own Page token automatically.
- **16 tools** covering posts, scheduling, photos, Reels, comments, moderation and insights.
- **Safe by default:** tools are labelled read-only or destructive (MCP
  annotations), a `--read-only` mode hides write tools, requests are signed
  with `appsecret_proof`, and tokens never appear in URLs or logs.
- **Runs anywhere:** stdio for desktop clients, streamable HTTP (with optional
  bearer auth) for remote clients, or the Docker image.
- **Production-quality code:** typed (`mypy --strict`), layered architecture,
  and over 95% test coverage against a mocked Graph API.

## Quick start

**1. Get a token.** Create a Meta app and generate an access token with the Page
permissions listed in **[docs/setup-meta-app.md](docs/setup-meta-app.md)**.
This takes about 5 minutes.

**2. Add the server to your MCP client.** You'll need [uv](https://docs.astral.sh/uv/).
For example, in Claude Desktop's `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "facebook": {
      "command": "uvx",
      "args": ["facebook-mcp"],
      "env": {
        "FB_USER_ACCESS_TOKEN": "your-long-lived-user-token",
        "FB_APP_SECRET": "your-app-secret"
      }
    }
  }
}
```

Config for every other client (Claude Code, ChatGPT, Gemini CLI, Cursor,
VS Code, Docker) is in **[docs/clients.md](docs/clients.md)**.

**3. Ask your assistant** something like "Which Facebook Pages can you manage?"

## Tools

Every tool except `list_pages` accepts an optional `page` (a Page id or exact
name). Leave it out and the server uses the default Page. For post ids, it uses
the Page that owns the post.

| Tool | Type | Description |
|---|---|---|
| `list_pages` | read | Pages this server can manage |
| `get_page_info` | read | Name, category, about, link, fans and followers |
| `list_posts` | read | Published posts with reaction, comment and share counts (paginated) |
| `list_scheduled_posts` | read | Scheduled, not-yet-published posts |
| `get_post` | read | One post with engagement counts |
| `create_post` | write | Publish or schedule a text/link post |
| `create_photo_post` | write | Publish a photo from a public URL |
| `create_reel` | write | Upload a local video and publish or schedule it as a Reel |
| `update_post` | write | Edit a post's text |
| `delete_post` | destructive | Delete a post |
| `list_comments` | read | Comments on a post, or replies to a comment (paginated) |
| `add_comment` | write | Comment as the Page, or reply to a comment |
| `set_comment_hidden` | write | Hide or unhide a comment |
| `delete_comment` | destructive | Delete a comment |
| `get_page_insights` | read | Page analytics over a period or date range |
| `get_post_insights` | read | Analytics for one post |

## Configuration

Settings come from environment variables, or from a `.env` file in the working
directory (see [`.env.example`](.env.example)).

| Variable | Default | Description |
|---|---|---|
| `FB_USER_ACCESS_TOKEN` | | **Multi-page mode.** A long-lived user token; every Page you manage is discovered. |
| `FB_PAGE_ID` + `FB_PAGE_ACCESS_TOKEN` | | **Single-page mode.** Use instead of the user token. |
| `FB_DEFAULT_PAGE` | | Page id or name to use when a tool call doesn't name one |
| `FB_APP_SECRET` | | Your app secret. Turns on `appsecret_proof` signing (recommended). |
| `FB_GRAPH_API_VERSION` | `v26.0` | Graph API version |
| `FB_TIMEOUT` | `30` | Graph request timeout, in seconds |
| `FB_UPLOAD_TIMEOUT` | `900` | Timeout for sending and confirming video/file uploads, in seconds |
| `MCP_TRANSPORT` | `stdio` | `stdio` or `http` |
| `MCP_HOST` / `MCP_PORT` / `MCP_PATH` | `127.0.0.1` / `8000` / `/mcp` | HTTP transport only |
| `MCP_AUTH_TOKEN` | | HTTP only: require `Authorization: Bearer <token>` |
| `MCP_READ_ONLY` | `false` | Hide every write tool |
| `MCP_LOG_LEVEL` | `INFO` | Log level (logs go to stderr) |

CLI flags override environment variables:

```bash
facebook-mcp --transport http --port 8000 --read-only
facebook-mcp exchange-token --app-id 123 --token SHORT_LIVED_TOKEN   # reads FB_APP_SECRET
```

## Security

- Use `--read-only` until you trust your setup.
- Always set `MCP_AUTH_TOKEN` when serving over HTTP, and never expose an
  unauthenticated server to the internet.
- Turn on **Require App Secret** in your Meta app's advanced settings, so a
  leaked token can't be used without your app secret.
- Never commit tokens. `.env` is git-ignored.

To report a vulnerability, see [SECURITY.md](SECURITY.md).

## Documentation

- [Setting up a Meta app and tokens](docs/setup-meta-app.md)
- [Connecting MCP clients](docs/clients.md)
- [Architecture and design](docs/architecture.md)

## Contributing

Contributions are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) for the dev
setup and guidelines. In short: `uv sync`, then `uv run pytest`.

## License

[MIT](LICENSE) © Salinda Hulangamuwa

*This is an independent project. It is not affiliated with, endorsed by, or
sponsored by Meta Platforms, Inc. Facebook is a trademark of Meta Platforms, Inc.*
