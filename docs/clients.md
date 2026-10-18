# Connecting MCP clients

Every example below runs the published package with
[`uvx`](https://docs.astral.sh/uv/guides/tools/), so you don't need to clone or
install anything manually. To run the latest unreleased code instead, replace
`"facebook-mcp"` with
`"--from", "git+https://github.com/SalindaHulangamuwa/facebook-mcp", "facebook-mcp"`.

Replace the token values with your own (see [setup-meta-app.md](setup-meta-app.md)).
For single-page mode, use `FB_PAGE_ID` and `FB_PAGE_ACCESS_TOKEN` in place of
`FB_USER_ACCESS_TOKEN`.

---

## 1. Prerequisites: Install `uv`

`uv` provides `uvx`, the fast tool runner used to run `facebook-mcp`.

### macOS & Linux
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
# Or on macOS with Homebrew: brew install uv
```
Find your absolute `uvx` path:
```bash
which uvx
# Typically: /Users/<your-user>/.local/bin/uvx (macOS)
# Or:        /home/<your-user>/.local/bin/uvx (Linux)
```

### Windows
Run in PowerShell:
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
# Or using winget: winget install --id=astral-sh.uv
```
Find your absolute `uvx` path in PowerShell:
```powershell
(Get-Command uvx).Source
# Typically: C:\Users\<your-user>\AppData\Local\bin\uvx.exe
```

> **Why the full path is recommended for desktop apps:**  
> Desktop GUI applications (such as Claude Desktop) do not inherit your terminal's shell `$PATH` profile. Using the absolute path prevents `command not found: uvx` errors.

---

## 2. Client Configurations

### Claude Desktop

Open your configuration file (or go to **Claude menu → Settings → Developer → Edit Config**):
* **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
* **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
* **Linux:** `~/.config/Claude/claude_desktop_config.json`

#### macOS / Linux
```json
{
  "mcpServers": {
    "facebook": {
      "command": "/Users/<your-user>/.local/bin/uvx",
      "args": ["facebook-mcp"],
      "env": {
        "FB_USER_ACCESS_TOKEN": "your-user-token",
        "FB_APP_SECRET": "your-app-secret"
      }
    }
  }
}
```

#### Windows
*(Use double backslashes `\\` for the executable path)*
```json
{
  "mcpServers": {
    "facebook": {
      "command": "C:\\Users\\<your-user>\\AppData\\Local\\bin\\uvx.exe",
      "args": ["facebook-mcp"],
      "env": {
        "FB_USER_ACCESS_TOKEN": "your-user-token",
        "FB_APP_SECRET": "your-app-secret"
      }
    }
  }
}
```

> **Important:** Fully quit and restart Claude Desktop (**Cmd + Q** on Mac, or Exit from the system tray on Windows) after saving.

---

### Claude Code (CLI)

Run in your terminal:
```bash
claude mcp add facebook \
  -e FB_USER_ACCESS_TOKEN=your-user-token -e FB_APP_SECRET=your-app-secret \
  -- uvx facebook-mcp
```

---

### Cursor

Add to your config file:
* **macOS / Linux:** `~/.cursor/mcp.json` (global) or `.cursor/mcp.json` (workspace)
* **Windows:** `%USERPROFILE%\.cursor\mcp.json`

```json
{
  "mcpServers": {
    "facebook": {
      "command": "uvx",
      "args": ["facebook-mcp"],
      "env": {
        "FB_USER_ACCESS_TOKEN": "your-user-token",
        "FB_APP_SECRET": "your-app-secret"
      }
    }
  }
}
```

---

### VS Code (GitHub Copilot agent mode)

In your workspace root, create or edit `.vscode/mcp.json`:

```json
{
  "servers": {
    "facebook": {
      "type": "stdio",
      "command": "uvx",
      "args": ["facebook-mcp"],
      "env": {
        "FB_USER_ACCESS_TOKEN": "your-user-token",
        "FB_APP_SECRET": "your-app-secret"
      }
    }
  }
}
```

---

### Gemini CLI

In `~/.gemini/settings.json`:

```json
{
  "mcpServers": {
    "facebook": {
      "command": "uvx",
      "args": ["facebook-mcp"],
      "env": {
        "FB_USER_ACCESS_TOKEN": "your-user-token",
        "FB_APP_SECRET": "your-app-secret"
      }
    }
  }
}
```

---

### Remote clients over HTTP (ChatGPT and others)

Start the server with the HTTP transport and a bearer token:

```bash
export FB_USER_ACCESS_TOKEN=... FB_APP_SECRET=...
export MCP_AUTH_TOKEN=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
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

#### ChatGPT

ChatGPT only connects to public HTTPS servers:

1. Expose the local server through a tunnel, e.g.
   `cloudflared tunnel --url http://127.0.0.1:8000` or `ngrok http 8000`.
2. In ChatGPT, turn on Developer mode (Settings → Apps & Connectors → Advanced),
   create a connector, and enter `https://<your-tunnel-host>/mcp`.

> **Security Note:** ChatGPT's connector UI does not send static bearer tokens. If you expose the server without `MCP_AUTH_TOKEN`, anyone with the URL can act on your Pages. Run with `--read-only`, keep the URL private, and stop the tunnel when finished.

---

## 3. Docker (Any OS)

Run the containerized version on any OS without installing Python or `uv`:

```bash
docker run --rm -p 8000:8000 \
  -e FB_USER_ACCESS_TOKEN=... -e FB_APP_SECRET=... -e MCP_AUTH_TOKEN=... \
  ghcr.io/salindahulangamuwa/facebook-mcp
```

Or build locally:
```bash
docker build -t facebook-mcp .
```

---

## 4. Debugging with MCP Inspector

Test and inspect the available tools interactively in your browser:

```bash
npx @modelcontextprotocol/inspector uvx facebook-mcp
```
