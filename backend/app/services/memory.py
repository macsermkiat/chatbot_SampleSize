"""Chat memory backed by PostgreSQL with in-memory fallback.

Uses LangGraph's built-in AsyncPostgresSaver for checkpoint persistence.
Falls back to MemorySaver when PostgreSQL is unavailable (dev mode).
Also provides a thin wrapper for the 20-message sliding window that matches
the n8n ``contextWindowLength: 20`` configuration.
"""

from __future__ import annotations

import logging
from typing import Union
from urllib.parse import urlparse

from langchain_core.messages import AnyMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from psycopg import AsyncConnection
from psycopg.rows import dict_row

from app.config import settings

WINDOW_SIZE = 20

_logger = logging.getLogger(__name__)

# Module-level references managed by open_checkpointer / close_checkpointer.
_checkpointer: Union[AsyncPostgresSaver, MemorySaver, None] = None
_pg_conn: AsyncConnection | None = None


def _connect_kwargs() -> dict:
    """Build extra kwargs for psycopg AsyncConnection based on the DSN."""
    kwargs: dict = {}
    parsed = urlparse(settings.database_dsn)
    hostname = parsed.hostname or ""

    if ".supabase.co" in hostname or ".supabase.com" in hostname:
        kwargs["sslmode"] = "require"

    # TCP keepalive to prevent Supabase from dropping idle connections
    kwargs["keepalives"] = 1
    kwargs["keepalives_idle"] = 30
    kwargs["keepalives_interval"] = 10
    kwargs["keepalives_count"] = 3

    return kwargs


async def open_checkpointer() -> Union[AsyncPostgresSaver, MemorySaver]:
    """Open the checkpointer connection and create checkpoint tables.

    Call once during app startup (lifespan).  The returned saver is also
    stored at module level so ``get_checkpointer()`` can hand it out.

    Falls back to an in-memory saver when PostgreSQL is unavailable.
    """
    global _checkpointer, _pg_conn

    if not settings.has_database:
        _logger.info("No DATABASE_URL configured, using in-memory checkpointer")
        mem = MemorySaver()
        _checkpointer = mem
        return mem

    try:
        extra = _connect_kwargs()
        conn = await AsyncConnection.connect(
            settings.database_dsn,
            autocommit=True,
            prepare_threshold=0,
            row_factory=dict_row,
            **extra,
        )
        _pg_conn = conn

        saver = AsyncPostgresSaver(conn=conn)
        await saver.setup()
        _checkpointer = saver

        is_supabase = ".supabase.co" in (urlparse(settings.database_dsn).hostname or "")
        label = "PostgreSQL (Supabase)" if is_supabase else "PostgreSQL"
        _logger.info("Checkpointer: %s", label)
        return saver
    except Exception as exc:
        _logger.warning("PostgreSQL unavailable (%s), using in-memory checkpointer", exc)
        mem = MemorySaver()
        _checkpointer = mem
        return mem


async def close_checkpointer() -> None:
    """Tear down the checkpointer connection.

    Call once during app shutdown (lifespan).
    """
    global _checkpointer, _pg_conn
    if _pg_conn is not None:
        try:
            await _pg_conn.close()
        except Exception:
            pass
        _pg_conn = None
    _checkpointer = None


def get_checkpointer() -> Union[AsyncPostgresSaver, MemorySaver]:
    """Return the active checkpointer.

    Raises RuntimeError if called before ``open_checkpointer()``.
    """
    if _checkpointer is None:
        raise RuntimeError(
            "Checkpointer not initialised. "
            "Ensure open_checkpointer() is called during app startup."
        )
    return _checkpointer


def trim_messages(messages: list[AnyMessage], window: int = WINDOW_SIZE) -> list[AnyMessage]:
    """Keep the most recent *window* messages (matching the n8n sliding-window config).

    Always preserves the system message at index 0 if present.
    """
    if len(messages) <= window:
        return list(messages)

    # Preserve system message if it exists at position 0
    first = messages[0]
    if getattr(first, "type", None) == "system":
        return [first, *messages[-(window - 1):]]

    return list(messages[-window:])
