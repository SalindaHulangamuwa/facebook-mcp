"""Single place where domain/infrastructure errors become client-facing ToolErrors.

FastMCP masks unexpected exceptions (`mask_error_details=True`), which is the
right default. Errors we *understand* should instead reach the AI client with
an actionable message, so every tool is wrapped by `translate_errors`. Tool
bodies therefore never need their own try/except blocks.
"""

from __future__ import annotations

import functools
import logging
from collections.abc import Awaitable, Callable
from typing import ParamSpec, TypeVar

from fastmcp.exceptions import ToolError
from pydantic import ValidationError

from facebook_mcp.exceptions import FacebookMCPError
from facebook_mcp.graph import GraphAPIError

P = ParamSpec("P")
R = TypeVar("R")

logger = logging.getLogger(__name__)


def translate_errors(fn: Callable[P, Awaitable[R]]) -> Callable[P, Awaitable[R]]:
    @functools.wraps(fn)
    async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        try:
            return await fn(*args, **kwargs)
        except GraphAPIError as exc:
            logger.warning(
                "Graph API error in %s: code=%s fbtrace_id=%s",
                fn.__name__,
                exc.code,
                exc.fbtrace_id,
            )
            raise ToolError(exc.user_message) from exc
        except FacebookMCPError as exc:
            raise ToolError(exc.user_message) from exc
        except ValidationError as exc:
            raise ToolError(describe_validation_error(exc)) from exc

    return wrapper


def describe_validation_error(exc: ValidationError) -> str:
    problems = "; ".join(error["msg"] for error in exc.errors())
    return f"Invalid input: {problems}"
