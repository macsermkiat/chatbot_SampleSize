"""Methodology phase nodes: agent + secretary."""

from __future__ import annotations

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from app.agents.prompts import METHODOLOGY_PROMPT, METHODOLOGY_SECRETARY_PROMPT
from app.agents.state import MethodologyOutput, ResearchState, SecretaryOutput
from app.services.llm import get_chat_model
from app.services.memory import trim_messages


# ---------------------------------------------------------------------------
# 1. MethodologyAgent -- study design, DAGs, bias detection
# ---------------------------------------------------------------------------

async def methodology_node(state: ResearchState) -> dict:
    """Design rigorous research protocols and critique study methodologies."""

    llm = get_chat_model("methodology").with_structured_output(MethodologyOutput)

    user_text = _build_input_text(state)
    messages = [
        SystemMessage(content=METHODOLOGY_PROMPT),
        *trim_messages(state["messages"]),
        HumanMessage(content=user_text),
    ]

    result: MethodologyOutput = await llm.ainvoke(messages)

    return {
        "messages": [AIMessage(content=result.direct_response_to_user)],
        "agent_to_route_to": result.agent_to_route_to,
        "forwarded_message": result.forwarded_message,
    }


# ---------------------------------------------------------------------------
# 2. MethodologySecretary -- summarize and route
# ---------------------------------------------------------------------------

async def methodology_secretary_node(state: ResearchState) -> dict:
    """Summarize methodology output and decide next phase."""

    llm = get_chat_model("methodology_secretary").with_structured_output(SecretaryOutput)

    user_text = _build_input_text(state)
    messages = [
        SystemMessage(content=METHODOLOGY_SECRETARY_PROMPT),
        HumanMessage(content=user_text),
    ]

    result: SecretaryOutput = await llm.ainvoke(messages)

    return {
        "messages": [AIMessage(content=result.direct_response_to_user)],
        "agent_to_route_to": result.agent_to_route_to,
        "forwarded_message": result.forwarded_message,
    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _build_input_text(state: ResearchState) -> str:
    forwarded = state.get("forwarded_message", "") or "-"
    user_msg = "-"
    for msg in reversed(state.get("messages", [])):
        if getattr(msg, "type", None) == "human":
            user_msg = msg.content
            break
    return f"Query from other agent: {forwarded}\n\nUser response: {user_msg}"
