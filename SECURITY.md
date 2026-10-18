# Security Policy

facebook-mcp can publish and delete content on real Facebook Pages, so we take
security seriously.

## Supported versions

Security fixes go into the latest release only.

## Reporting a vulnerability

**Please don't open a public issue.** Report vulnerabilities privately through
[GitHub Security Advisories](https://github.com/SalindaHulangamuwa/facebook-mcp/security/advisories/new).

Include steps to reproduce, the affected version, and the impact. You'll get an
acknowledgement within 72 hours and a fix or mitigation plan as soon as
possible. We're happy to credit you in the release notes.

## Your responsibilities as a user

- **Treat access tokens and the app secret like passwords.** Never commit
  them, paste them into issues, or share screenshots that show them. If one
  leaks, regenerate it right away and reset the app secret in the Meta
  developer dashboard.
- Turn on **Require App Secret** in your Meta app's settings, and set
  `FB_APP_SECRET` so every request is signed.
- Always set `MCP_AUTH_TOKEN` when using the HTTP transport, and don't expose
  an unauthenticated server to the internet.
- Use `--read-only` for assistants that only need analytics.
- Grant the token only the permissions you need.
