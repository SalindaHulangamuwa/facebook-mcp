# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project uses
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- `create_reel` tool: uploads a local video through the Reels resumable upload
  flow and publishes or schedules it on a Page.

## [0.1.0] - 2026-10-18

### Added

- First public release.
- 15 MCP tools for Pages, posts (including scheduling and photos), comments,
  moderation and insights.
- Multi-page mode (`FB_USER_ACCESS_TOKEN`, Pages discovered via `/me/accounts`)
  and single-page mode (`FB_PAGE_ID` + `FB_PAGE_ACCESS_TOKEN`).
- Page resolution by id, name, owning post id, `FB_DEFAULT_PAGE`, or the only
  available Page.
- stdio and streamable HTTP transports, with optional bearer-token auth.
- `--read-only` mode, MCP tool annotations, `appsecret_proof` request signing.
- `facebook-mcp exchange-token` helper for long-lived tokens.
- Docker image.

[Unreleased]: https://github.com/SalindaHulangamuwa/facebook-mcp/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/SalindaHulangamuwa/facebook-mcp/releases/tag/v0.1.0
