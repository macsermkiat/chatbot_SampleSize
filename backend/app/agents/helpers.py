"""Shared helper functions used across agent nodes.

Consolidates duplicated logic (input text building, AI output collection)
into a single module.
"""

from __future__ import annotations

from app.agents.state import ResearchState


_MAX_FILE_CHARS = 30_000  # ~7,500 tokens -- safe for all providers


def build_input_text(state: ResearchState) -> str:
    """Build the input text block from forwarded message + latest user message.

    Replaces the per-module ``_build_input_text()`` duplicated in
    research_gap.py, methodology.py, and biostatistics.py.
    """
    forwarded = state.get("forwarded_message", "") or "-"
    user_msg = get_latest_user_message(state)
    parts = [f"Query from other agent: {forwarded}", f"User response: {user_msg}"]

    uploaded = state.get("uploaded_files", [])
    if uploaded:
        file_sections = []
        for f in uploaded:
            name = f.get("filename", "unknown")
            text = f.get("extracted_text", "")
            if len(text) > _MAX_FILE_CHARS:
                text = (
                    text[:_MAX_FILE_CHARS]
                    + f"\n\n[Truncated: showing first {_MAX_FILE_CHARS:,} of {len(text):,} characters]"
                )
            file_sections.append(f"[Uploaded file: {name}]\n{text}")
        parts.append("Uploaded documents:\n" + "\n\n".join(file_sections))

    return "\n\n".join(parts)


def get_latest_user_message(state: ResearchState) -> str:
    """Return the content of the most recent human message, or '-' if none."""
    for msg in reversed(state.get("messages", [])):
        if getattr(msg, "type", None) == "human":
            return msg.content
    return "-"
