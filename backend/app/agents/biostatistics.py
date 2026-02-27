"""Biostatistics phase nodes: agent, diagnostic tool, coding agent, secretary, routing."""

from __future__ import annotations

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from app.agents.prompts import (
    BIOSTATS_PROMPT,
    BIOSTATS_ROUTING_PROMPT,
    BIOSTATS_SECRETARY_PROMPT,
    CODING_PROMPT,
    DIAGNOSTIC_PROMPT,
)
from app.agents.state import (
    BiostatisticsOutput,
    CodingOutput,
    ResearchState,
    RoutingOutput,
    SecretaryOutput,
)
from app.services.llm import get_chat_model
from app.services.memory import trim_messages


# ---------------------------------------------------------------------------
# 1. BiostatisticsAgent -- power/sample size, clarification loop
# ---------------------------------------------------------------------------

async def biostatistics_node(state: ResearchState) -> dict:
    """Guide through statistical lifecycle: power analysis, study design, interpretation."""

    llm = get_chat_model("biostatistics").with_structured_output(BiostatisticsOutput)

    user_text = _build_input_text(state)
    messages = [
        SystemMessage(content=BIOSTATS_PROMPT),
        *trim_messages(state["messages"]),
        HumanMessage(content=user_text),
    ]

    result: BiostatisticsOutput = await llm.ainvoke(messages)

    return {
        "messages": [AIMessage(content=result.direct_response_to_user)],
        "need_info": result.need_info,
        "forwarded_message": result.forwarded_message,
    }


# ---------------------------------------------------------------------------
# 2. DiagnosticTool -- statistical test selection (used as tool, not standalone)
# ---------------------------------------------------------------------------

async def diagnostic_node(state: ResearchState) -> dict:
    """Recommend appropriate statistical test based on variable types and distributions."""

    llm = get_chat_model("diagnostic")

    user_text = _build_input_text(state)
    messages = [
        SystemMessage(content=DIAGNOSTIC_PROMPT),
        HumanMessage(content=user_text),
    ]

    response = await llm.ainvoke(messages)

    return {
        "messages": [AIMessage(content=response.content)],
    }


# ---------------------------------------------------------------------------
# 3. CodingAgent -- Python/R/STATA code generation
# ---------------------------------------------------------------------------

async def coding_node(state: ResearchState) -> dict:
    """Generate statistical code based on biostatistics agent instructions."""

    llm = get_chat_model("coding").with_structured_output(CodingOutput)

    instruction = state.get("forwarded_message", "")
    messages = [
        SystemMessage(content=CODING_PROMPT),
        *trim_messages(state["messages"]),
        HumanMessage(content=f"Instruction: {instruction}"),
    ]

    result: CodingOutput = await llm.ainvoke(messages)

    code_output = {}
    if result.need_code:
        code_output = {
            "session_id": result.session_id or state.get("session_id", ""),
            "language": result.language,
            "script": result.script,
        }

    return {
        "messages": [AIMessage(content=result.direct_response_to_user)],
        "need_code": result.need_code,
        "code_output": code_output,
        "forwarded_message": result.forwarded_message,
    }


# ---------------------------------------------------------------------------
# 4. BiostatsSecretary -- summarize and ask next step
# ---------------------------------------------------------------------------

async def biostats_secretary_node(state: ResearchState) -> dict:
    """Summarize biostatistics/coding output and ask user what to do next."""

    llm = get_chat_model("biostats_secretary").with_structured_output(SecretaryOutput)

    # Build input from both coding and biostats agent outputs (matching n8n template)
    forwarded = state.get("forwarded_message", "") or "-"
    messages = [
        SystemMessage(content=BIOSTATS_SECRETARY_PROMPT),
        HumanMessage(content=f"Input from agents: {forwarded}"),
    ]

    result: SecretaryOutput = await llm.ainvoke(messages)

    return {
        "messages": [AIMessage(content=result.direct_response_to_user)],
        "agent_to_route_to": result.agent_to_route_to,
        "forwarded_message": result.forwarded_message,
    }


# ---------------------------------------------------------------------------
# 5. BiostatsRouting -- decide next phase based on secretary output
# ---------------------------------------------------------------------------

async def biostats_routing_node(state: ResearchState) -> dict:
    """Route user to the appropriate next phase after biostatistics."""

    llm = get_chat_model("biostats_routing").with_structured_output(RoutingOutput)

    user_text = _build_input_text(state)
    messages = [
        SystemMessage(content=BIOSTATS_ROUTING_PROMPT),
        HumanMessage(content=user_text),
    ]

    result: RoutingOutput = await llm.ainvoke(messages)

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
