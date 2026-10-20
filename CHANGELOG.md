# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project uses
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.3.1] - 2026-10-20

### Fixed

- `create_reel` no longer times out on larger videos. Uploads use a separate
  `FB_UPLOAD_TIMEOUT` (default 900 s) instead of the 30 s API timeout, stream
  the file in 4 MB chunks instead of loading it into memory, and report upload
  progress to the MCP client.
- Timeouts now surface as a clear `GraphTimeoutError` with a hint, instead of
  an empty connection error.

## [0.3.0] - 2026-10-19

### Added

- `create_photo_post` accepts `image_path` to upload a local image file, and
  `scheduled_time` to schedule photo posts.

## [0.2.0] - 2026-10-19

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

[Unreleased]: https://github.com/SalindaHulangamuwa/facebook-mcp/compare/v0.3.0...HEAD
[0.3.0]: https://github.com/SalindaHulangamuwa/facebook-mcp/releases/tag/v0.3.0
[0.2.0]: https://github.com/SalindaHulangamuwa/facebook-mcp/releases/tag/v0.2.0
[0.1.0]: https://github.com/SalindaHulangamuwa/facebook-mcp/releases/tag/v0.1.0
