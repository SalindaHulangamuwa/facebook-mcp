"""Streaming local files to Facebook upload endpoints.

Videos can be hundreds of megabytes. Streaming them in chunks keeps memory flat
and lets callers report progress, which also keeps MCP clients from giving up
on a long-running tool call.
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Awaitable, Callable
from pathlib import Path

ProgressCallback = Callable[[int, int], Awaitable[None]]
"""Called with (bytes_sent, total_bytes) after each chunk."""

UPLOAD_CHUNK_BYTES = 4 * 1024 * 1024


async def ignore_progress(_sent: int, _total: int) -> None:
    """Default progress callback: report nothing."""


async def stream_file(
    path: Path,
    on_progress: ProgressCallback = ignore_progress,
    chunk_size: int = UPLOAD_CHUNK_BYTES,
) -> AsyncIterator[bytes]:
    """Yield `path` in chunks without blocking the event loop."""
    total = path.stat().st_size
    sent = 0
    with path.open("rb") as file:
        while chunk := await asyncio.to_thread(file.read, chunk_size):
            yield chunk
            sent += len(chunk)
            await on_progress(sent, total)
