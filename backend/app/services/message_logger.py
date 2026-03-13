"""Fire-and-forget message logger for reviewable chat history."""

from __future__ import annotations

import asyncio
import logging

from app.db import get_pool

_logger = logging.getLogger(__name__)

_INSERT_SQL = """
    INSERT INTO message_logs (session_id, role, content, node, phase)
    VALUES ($1, $2, $3, $4, $5)
"""


async def _write_log(
    session_id: str,
    role: str,
    content: str,
    node: str | None = None,
    phase: str | None = None,
) -> None:
    """Persist a single message row. Called as a background task."""
    try:
        pool = await get_pool()
        await pool.execute(_INSERT_SQL, session_id, role, content, node, phase)
    except Exception:
        _logger.warning("Failed to log message for session %s", session_id, exc_info=True)


def log_message(
    session_id: str,
    role: str,
    content: str,
    node: str | None = None,
    phase: str | None = None,
) -> None:
    """Schedule a message log write without blocking the caller."""
    asyncio.create_task(_write_log(session_id, role, content, node, phase))


# ---------------------------------------------------------------------------
# Token usage logging
# ---------------------------------------------------------------------------

_INSERT_TOKEN_SQL = """
    INSERT INTO token_logs (session_id, node, model, prompt_tokens, completion_tokens, total_tokens)
    VALUES ($1, $2, $3, $4, $5, $6)
"""


async def _write_token_log(
    session_id: str,
    node: str | None,
    model: str | None,
    prompt_tokens: int,
    completion_tokens: int,
    total_tokens: int,
) -> None:
    """Persist a single token usage row. Called as a background task."""
    try:
        pool = await get_pool()
        await pool.execute(
            _INSERT_TOKEN_SQL,
            session_id, node, model,
            prompt_tokens, completion_tokens, total_tokens,
        )
    except Exception:
        _logger.warning(
            "Failed to log tokens for session %s node %s",
            session_id, node, exc_info=True,
        )


def log_tokens(
    session_id: str,
    node: str | None = None,
    model: str | None = None,
    prompt_tokens: int = 0,
    completion_tokens: int = 0,
    total_tokens: int = 0,
) -> None:
    """Schedule a token usage log write without blocking the caller."""
    if total_tokens == 0 and (prompt_tokens + completion_tokens) == 0:
        return
    asyncio.create_task(
        _write_token_log(session_id, node, model, prompt_tokens, completion_tokens, total_tokens),
    )
