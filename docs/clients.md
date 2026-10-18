# Connecting MCP clients

Every example below runs the published package with
[`uvx`](https://docs.astral.sh/uv/guides/tools/), so you don't need to clone or
install anything. To run the latest unreleased code instead, replace
`"facebook-mcp"` with
`"--from", "git+https://github.com/SalindaHulangamuwa/facebook-mcp", "facebook-mcp"`.

Replace the token values with your own (see [setup-meta-app.md](setup-meta-app.md)).
For single-page mode, use `FB_PAGE_ID` and `FB_PAGE_ACCESS_TOKEN` in place of
`FB_USER_ACCESS_TOKEN`.

> Some desktop apps don't inherit your shell's `PATH`. If `uvx` isn't found,
> use its absolute path (`which uvx`, e.g. `/Users/you/.local/bin/uvx`).

## Claude Desktop

Settings → Developer → Edit Config (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "facebook": {
      "command": "uvx",
      "args": ["facebook-mcp"],
      "env": {
        "FB_USER_ACCESS_TOKEN": "...",
        "FB_APP_SECRET": "..."
      }
    }
  }
}
```

Restart Claude Desktop after saving.

## Claude Code

```bash
claude mcp add facebook \
  -e FB_USER_ACCESS_TOKEN=... -e FB_APP_SECRET=... \
  -- uvx facebook-mcp
```

## Cursor

`~/.cursor/mcp.json` (global) or `.cursor/mcp.json` (project). Use the same
JSON as Claude Desktop.

## VS Code (GitHub Copilot agent mode)

`.vscode/mcp.json`:

```json
{
  "servers": {
    "facebook": {
      "type": "stdio",
      "command": "uvx",
      "args": ["facebook-mcp"],
      "env": { "FB_USER_ACCESS_TOKEN": "...", "FB_APP_SECRET": "..." }
    }
  }
}
```

## Gemini CLI

`~/.gemini/settings.json`:

```json
{
  "mcpServers": {
    "facebook": {
      "command": "uvx",
      "args": ["facebook-mcp"],
      "env": { "FB_USER_ACCESS_TOKEN": "...", "FB_APP_SECRET": "..." }
    }
  }
}
```

## Remote clients over HTTP (ChatGPT and others)

Start the server with the HTTP transport and a bearer token:

```bash
export FB_USER_ACCESS_TOKEN=... FB_APP_SECRET=...
export MCP_AUTH_TOKEN=$(python -c "import secrets; print(secrets.token_urlsafe(32))")
uvx facebook-mcp --transport http --port 8000
```

Clients that support custom headers connect to `http://127.0.0.1:8000/mcp`
and send `Authorization: Bearer $MCP_AUTH_TOKEN`. For example, in Gemini CLI:

```json
{
  "mcpServers": {
    "facebook": {
      "httpUrl": "http://127.0.0.1:8000/mcp",
      "headers": { "Authorization": "Bearer YOUR_MCP_AUTH_TOKEN" }
    }
  }
}
```

### ChatGPT

ChatGPT only connects to public HTTPS servers.

1. Expose the local server through a tunnel, e.g.
   `cloudflared tunnel --url http://127.0.0.1:8000` or `ngrok http 8000`.
2. In ChatGPT, turn on Developer mode (Settings → Apps & Connectors → Advanced),
   create a connector, and enter `https://<your-tunnel-host>/mcp`.

ChatGPT's connector UI supports OAuth or no authentication. It can't send a
static bearer token. If you expose the server without `MCP_AUTH_TOKEN`,
**anyone who has the URL can act on your Pages**. Run with `--read-only`, keep
the URL private, and stop the tunnel when you're done. For a permanent
deployment, put an OAuth provider in front (FastMCP supports GitHub, Google,
Auth0, WorkOS and others).

## Docker

```bash
docker build -t facebook-mcp .
docker run --rm -p 8000:8000 \
  -e FB_USER_ACCESS_TOKEN=... -e FB_APP_SECRET=... -e MCP_AUTH_TOKEN=... \
  facebook-mcp
```

Published images are available at `ghcr.io/salindahulangamuwa/facebook-mcp`.

## Debugging

The MCP Inspector lets you browse and call tools by hand:

```bash
npx @modelcontextprotocol/inspector uvx facebook-mcp
```
