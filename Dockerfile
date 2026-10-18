# syntax=docker/dockerfile:1
# Runs facebook-mcp over streamable HTTP. Configure with environment variables:
#   docker run -p 8000:8000 -e FB_USER_ACCESS_TOKEN=... -e MCP_AUTH_TOKEN=... facebook-mcp

FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS build
WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
COPY pyproject.toml uv.lock README.md LICENSE ./
RUN uv sync --locked --no-dev --no-install-project
COPY src ./src
RUN uv sync --locked --no-dev

FROM python:3.12-slim-bookworm
RUN useradd --create-home --uid 10001 app
WORKDIR /app
COPY --from=build --chown=app:app /app /app
ENV PATH="/app/.venv/bin:$PATH" \
    MCP_TRANSPORT=http \
    MCP_HOST=0.0.0.0 \
    MCP_PORT=8000
USER app
EXPOSE 8000
ENTRYPOINT ["facebook-mcp"]
