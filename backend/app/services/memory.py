"""Chat memory backed by PostgreSQL.

Uses LangGraph's built-in AsyncPostgresSaver for checkpoint persistence.
Also provides a thin wrapper for the 20-message sliding window that matches
the n8n ``contextWindowLength: 20`` configuration.
"""

from __future__ import annotations

from langchain_core.messages import AnyMessage
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from app.config import settings

WINDOW_SIZE = 20

# Module-level reference managed by open_checkpointer / close_checkpointer.
_checkpointer: AsyncPostgresSaver | None = None


async def open_checkpointer() -> AsyncPostgresSaver:
    """Open the checkpointer connection and create checkpoint tables.

    Call once during app startup (lifespan).  The returned saver is also
    stored at module level so ``get_checkpointer()`` can hand it out.
    """
    global _checkpointer
    saver = AsyncPostgresSaver.from_conn_string(settings.database_url_sync)
    await saver.setup()
    _checkpointer = saver
    return saver


async def close_checkpointer() -> None:
    """Tear down the checkpointer connection.

    Call once during app shutdown (lifespan).
    """
    global _checkpointer
    if _checkpointer is not None:
        # AsyncPostgresSaver wraps a connection pool; closing is safe.
        try:
            await _checkpointer.conn.close()
        except Exception:
            pass
        _checkpointer = None


def get_checkpointer() -> AsyncPostgresSaver:
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
