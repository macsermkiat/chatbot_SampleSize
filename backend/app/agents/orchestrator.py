"""Orchestrator (supervisor) node -- triages and routes to specialist phases."""

from __future__ import annotations

import logging

from langchain_core.messages import AIMessage, SystemMessage

from app.agents.progress import emit_progress
from app.agents.prompt_composer import get_prompt
from app.agents.prompts import ORCHESTRATOR_PROMPT
from app.agents.state import OrchestratorOutput, ResearchState
from app.services.llm import get_structured_model
from app.services.memory import trim_messages

_logger = logging.getLogger(__name__)


def _sanitize_filename(name: str) -> str:
    """Strip control chars and truncate to prevent prompt injection via filename."""
    # Keep only printable ASCII and common unicode letters
    sanitized = "".join(ch for ch in name if ch.isprintable())
    return sanitized[:255]


def _build_file_context(uploaded_files: list[dict]) -> str:
    """Format uploaded file metadata for the orchestrator system prompt."""
    if not uploaded_files:
        return ""
    lines: list[str] = []
    for f in uploaded_files:
        name = _sanitize_filename(f.get("filename", "unknown"))
        text = f.get("extracted_text", "")
        char_count = len(text)
        lines.append(f"- {name} ({char_count:,} characters extracted)")
    return (
        "\n\nUploaded documents attached to this message:\n"
        + "\n".join(lines)
        + "\nThe user has attached these documents. Route with this context in mind."
    )


async def orchestrator_node(state: ResearchState) -> dict:
    """Triage the user's message and decide which specialist to route to."""

    llm = get_structured_model("orchestrator", OrchestratorOutput)

    expertise = state.get("expertise_level", "advanced")
    system_prompt = get_prompt(ORCHESTRATOR_PROMPT, expertise, "orchestrator")

    uploaded = state.get("uploaded_files", [])
    if uploaded:
        system_prompt = system_prompt + _build_file_context(uploaded)

    messages = trim_messages(state["messages"])
    prompt_messages = [SystemMessage(content=system_prompt), *messages]

    await emit_progress("Analyzing your request...")
    try:
        result: OrchestratorOutput = await llm.ainvoke(prompt_messages)
    except Exception as exc:
        _logger.exception("LLM call failed in orchestrator node")
        return {
            "messages": [AIMessage(content="I'm sorry, I encountered a temporary issue processing your request. Please try again.")],
            "current_phase": "orchestrator",
            "agent_to_route_to": "",
            "forwarded_message": "",
            "needs_clarification": False,
        }

    # When the orchestrator asks a clarification question, stay in orchestrator
    # so the user's reply routes back here instead of skipping to a specialist.
    if result.needs_clarification:
        return {
            "messages": [AIMessage(content=result.direct_response_to_user)],
            "current_phase": "orchestrator",
            "agent_to_route_to": "",
            "forwarded_message": "",
            "needs_clarification": True,
        }

    # Safety net: if the orchestrator's response ends with a question to the user
    # (e.g. "Which would you like next?"), do NOT route away -- wait for user reply.
    response_text = result.direct_response_to_user.strip()
    route_target = result.agent_to_route_to
    if route_target and response_text.endswith("?"):
        _logger.info(
            "Orchestrator response ends with question but set route=%r; "
            "overriding to stay and wait for user reply",
            route_target,
        )
        route_target = ""

    # agent_to_route_to now uses internal names directly (research_gap, etc.)
    next_phase = route_target or state.get("current_phase", "orchestrator")

    return {
        "messages": [AIMessage(content=result.direct_response_to_user)],
        "current_phase": next_phase,
        "agent_to_route_to": route_target,
        "forwarded_message": result.forwarded_message if route_target else "",
        "needs_clarification": False,
    }
