"""Thin helper for emitting real-time progress events to the SSE stream."""

from __future__ import annotations

import logging

from langchain_core.callbacks.manager import adispatch_custom_event

_logger = logging.getLogger(__name__)


async def emit_progress(status: str) -> None:
    """Emit a progress event that the SSE stream picks up as ``on_custom_event``.

    Silently no-ops when called outside a LangGraph run context (e.g. in unit
    tests that invoke node functions directly).
    """
    try:
        await adispatch_custom_event("progress", {"status": status})
    except RuntimeError:
        _logger.debug("emit_progress skipped (no active run context): %s", status)
