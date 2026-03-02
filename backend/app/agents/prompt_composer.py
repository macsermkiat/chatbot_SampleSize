"""Compose agent prompts based on expertise level.

Each agent's system prompt is built from:
  1. A global style directive (simple or advanced)
  2. The base domain prompt (always included -- contains routing logic)
  3. An optional per-agent addendum for simple mode
"""

from __future__ import annotations

from app.agents.prompts import (
    ADVANCED_STYLE_DIRECTIVE,
    SIMPLE_ADDENDA,
    SIMPLE_STYLE_DIRECTIVE,
)


def get_prompt(base_prompt: str, expertise_level: str, agent_name: str) -> str:
    """Return the full system prompt for *agent_name* at *expertise_level*.

    Parameters
    ----------
    base_prompt:
        The core domain prompt (e.g. ``ORCHESTRATOR_PROMPT``).
    expertise_level:
        ``"simple"`` or ``"advanced"``.  Falls back to ``"advanced"``
        for any unrecognised value.
    agent_name:
        Internal agent key (e.g. ``"orchestrator"``, ``"gap_summarize"``).
        Used to look up the per-agent simple-mode addendum.
    """
    if expertise_level == "simple":
        addendum = SIMPLE_ADDENDA.get(agent_name, "")
        return f"{SIMPLE_STYLE_DIRECTIVE}\n{base_prompt}{addendum}"

    return f"{ADVANCED_STYLE_DIRECTIVE}\n{base_prompt}"
