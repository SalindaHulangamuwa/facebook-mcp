# Contributing to facebook-mcp

Thanks for your interest. Bug reports, docs fixes and new tools are all welcome.

## Development setup

You'll need [uv](https://docs.astral.sh/uv/) and Python 3.10+.

```bash
git clone https://github.com/SalindaHulangamuwa/facebook-mcp
cd facebook-mcp
uv sync                      # creates .venv with runtime + dev dependencies
uv run pre-commit install    # optional: lint and format on every commit
```

## Checks (CI runs all of these)

```bash
uv run ruff check .          # lint, including complexity and security rules
uv run ruff format --check . # formatting
uv run mypy                  # strict type checking
uv run pytest --cov          # tests; coverage must stay at or above 85%
```

The tests never touch the real Graph API. They run the real server against an
in-memory fake (`tests/conftest.py::FakeGraph`), so they need no credentials.

To try your changes against a real Page, copy `.env.example` to `.env`, fill
it in, and run:

```bash
npx @modelcontextprotocol/inspector uv run facebook-mcp
```

## Guidelines

- **Read [docs/architecture.md](docs/architecture.md) first.** Keep tools thin.
  Logic belongs in services, transport concerns belong in `graph/`.
- **Keep it simple:** small functions, early returns, no deep nesting.
  `ruff` enforces a McCabe complexity limit.
- **Type everything.** `mypy --strict` must pass.
- **Test behaviour, not implementation.** Prefer calling tools through the MCP
  client fixture and asserting on the Graph request that was sent.
- **Give every write tool** a `tags={WRITE_TAG}` and accurate annotations.
- **Never log or return tokens.**
- **Update `CHANGELOG.md`** under *Unreleased* for any change users will notice.

## Pull requests

1. Fork the repo and create a branch from `main`.
2. Make your change with tests, and make sure all checks pass.
3. Open a PR describing the *what* and the *why*. Link any related issue.

Small, focused PRs get reviewed fastest. For larger changes, such as new
credential modes or new Graph API areas, open an issue first to agree on the design.

## Releasing (maintainers)

1. Bump `__version__` in `src/facebook_mcp/__init__.py` and move the
   *Unreleased* notes in `CHANGELOG.md` under the new version.
2. Commit, then tag: `git tag vX.Y.Z && git push --tags`.
3. The `release` workflow builds the package, publishes to PyPI (trusted
   publishing), pushes the Docker image to GHCR and creates a GitHub release.

By contributing, you agree that your contributions are licensed under the
[MIT License](LICENSE).
