"""Shared helper functions used across agent nodes.

Consolidates duplicated logic (input text building, AI output collection)
into a single module.
"""

from __future__ import annotations

from app.agents.state import ResearchState


def build_input_text(state: ResearchState) -> str:
    """Build the input text block from forwarded message + latest user message.

    Replaces the per-module ``_build_input_text()`` duplicated in
    research_gap.py, methodology.py, and biostatistics.py.
    """
    forwarded = state.get("forwarded_message", "") or "-"
    user_msg = get_latest_user_message(state)
    return f"Query from other agent: {forwarded}\n\nUser response: {user_msg}"


def get_latest_user_message(state: ResearchState) -> str:
    """Return the content of the most recent human message, or '-' if none."""
    for msg in reversed(state.get("messages", [])):
        if getattr(msg, "type", None) == "human":
            return msg.content
    return "-"
