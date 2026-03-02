"""Orchestrator (supervisor) node -- triages and routes to specialist phases."""

from __future__ import annotations

from langchain_core.messages import AIMessage, SystemMessage

from app.agents.prompt_composer import get_prompt
from app.agents.prompts import ORCHESTRATOR_PROMPT
from app.agents.state import OrchestratorOutput, ResearchState
from app.services.llm import get_chat_model
from app.services.memory import trim_messages


async def orchestrator_node(state: ResearchState) -> dict:
    """Triage the user's message and decide which specialist to route to."""

    llm = get_chat_model("orchestrator").with_structured_output(OrchestratorOutput)

    expertise = state.get("expertise_level", "advanced")
    system_prompt = get_prompt(ORCHESTRATOR_PROMPT, expertise, "orchestrator")

    messages = trim_messages(state["messages"])
    prompt_messages = [SystemMessage(content=system_prompt), *messages]

    result: OrchestratorOutput = await llm.ainvoke(prompt_messages)

    # agent_to_route_to now uses internal names directly (research_gap, etc.)
    next_phase = result.agent_to_route_to or state.get("current_phase", "orchestrator")

    return {
        "messages": [AIMessage(content=result.direct_response_to_user)],
        "current_phase": next_phase,
        "agent_to_route_to": result.agent_to_route_to,
        "forwarded_message": result.forwarded_message,
        "needs_clarification": result.needs_clarification,
    }
