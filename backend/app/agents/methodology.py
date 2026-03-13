"""Methodology phase node.

The secretary node has been removed -- the methodology agent now handles
routing decisions directly, reducing one LLM call per phase execution.
"""

from __future__ import annotations

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

import logging

from app.agents.helpers import build_input_text
from app.agents.progress import emit_progress
from app.agents.prompt_composer import get_prompt
from app.agents.prompts import METHODOLOGY_PROMPT
from app.agents.state import MethodologyOutput, ResearchState
from app.services.llm import get_structured_model
from app.services.memory import trim_messages

_logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# MethodologyAgent -- study design, DAGs, bias detection, routing
# ---------------------------------------------------------------------------

async def methodology_node(state: ResearchState) -> dict:
    """Design rigorous research protocols and decide next step.

    This node now also handles routing (previously done by the secretary).
    """

    llm = get_structured_model("methodology", MethodologyOutput)

    expertise = state.get("expertise_level", "advanced")
    user_text = build_input_text(state)
    messages = [
        SystemMessage(content=get_prompt(METHODOLOGY_PROMPT, expertise, "methodology")),
        *trim_messages(state["messages"]),
        HumanMessage(content=user_text),
    ]

    await emit_progress("Designing study methodology...")
    try:
        result: MethodologyOutput = await llm.ainvoke(messages)
    except Exception as exc:
        _logger.exception("LLM call failed in methodology node")
        return {
            "messages": [AIMessage(content="I'm sorry, I encountered a temporary issue while designing the methodology. Please try again.")],
            "needs_clarification": False,
            "agent_to_route_to": "",
            "current_phase": "methodology",
            "forwarded_message": "",
        }

    return {
        "messages": [AIMessage(content=result.direct_response_to_user)],
        "needs_clarification": result.needs_clarification,
        "agent_to_route_to": "" if result.needs_clarification else result.agent_to_route_to,
        "current_phase": result.agent_to_route_to or "methodology",
        "forwarded_message": result.forwarded_message,
    }
