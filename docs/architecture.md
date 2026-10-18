# Architecture

facebook-mcp has a small layered architecture. Each layer has one
responsibility, and dependencies only point inward.

```
 MCP client (Claude, ChatGPT, Gemini, ...)
        │  MCP (stdio / streamable HTTP)
┌───────▼────────────────────────────────────────────────────────┐
│ tools/       MCP adapters: input validation, annotations,      │
│              one-line delegation, uniform error translation    │
├────────────────────────────────────────────────────────────────┤
│ services/    Use cases: posts, comments, insights, page info   │
├────────────────────────────────────────────────────────────────┤
│ pages/       Which Page? Discovery (static or /me/accounts),   │
│              resolution by id/name/post-id/default, caching    │
├────────────────────────────────────────────────────────────────┤
│ domain/      Pydantic models: stable, flat output shapes       │
├────────────────────────────────────────────────────────────────┤
│ graph/       Graph API transport: pooling, auth header,        │
│              appsecret_proof, error-code → exception mapping   │
└────────────────────────────────────────────────────────────────┘
 server.py = composition root     cli.py = process entry point
```

## Request flow

`create_post(message="Hi", page="Acme Coffee")`:

1. **tools/posts.py** validates the arguments (length limits, URL, future
   schedule time) and calls `PostService.create_post`.
2. **services/posts.py** asks the `PageDirectory` to resolve `"Acme Coffee"`.
3. **pages/directory.py** loads Pages once (cached; `asyncio.Lock` prevents
   duplicate loads), matches by name, and returns a `PageSession` holding a
   `BoundGraph` for that Page's token.
4. The service calls `session.graph.post("<page_id>/feed", ...)`.
5. **graph/client.py** adds the bearer header and `appsecret_proof`, sends the
   request through the shared connection pool, and either returns JSON or
   raises a typed `GraphAPIError`.
6. The service turns the JSON into a `CreatedObject` model.
7. Errors from any layer derive from `FacebookMCPError`.
   **tools/errors.py** turns them into an MCP `ToolError` with an actionable
   message. Anything unexpected is masked by FastMCP.

## Design decisions

| Decision | Why |
|---|---|
| `GraphClient` is not bound to a token; `bind(token)` returns a `BoundGraph` | One connection pool serves every Page, and services never handle credentials. |
| Services depend on the `GraphGateway` protocol (`ports.py`) | Dependency inversion: services can be tested with any fake and don't know about HTTP. |
| `PageSource` strategy (`StaticPageSource`, `AccountsPageSource`) | Adding a credential mode (e.g. OAuth per user) means writing one new class. |
| Error translation in a decorator, not in each tool | No try/except boilerplate. Known errors carry a hint; unknown errors stay masked. |
| `AliasPath` in domain models | Nested Graph payloads are flattened declaratively, without hand-written parsing. |
| `build_server()` factory with an injectable `http_transport` | Tests run the real server end to end against a mocked Graph API, with no monkeypatching. |
| Tags plus `mcp.disable(tags={"write"})` | Read-only mode needs no conditionals in the tools. |
| Tokens in the `Authorization` header and `SecretStr` | Secrets stay out of URLs, logs and reprs. |

## Adding a tool

1. Add a method to the relevant service. Resolve the Page with
   `await self.pages.resolve(page, object_id=...)`.
2. Add or extend a domain model if the response has a new shape.
3. Register a thin tool in `tools/<area>.py` with `@tool(mcp, annotations=...)`.
   Add `tags={WRITE_TAG}` if it changes anything.
4. Add a test, usually one more `Route(...)` row in `tests/test_tools.py`.
