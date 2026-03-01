"""Biostatistics phase nodes: agent, diagnostic tool, coding agent.

Secretary and routing nodes have been removed -- the coding agent now
handles routing decisions directly via ``agent_to_route_to``.
"""

from __future__ import annotations

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from app.agents.helpers import build_input_text
from app.agents.prompts import BIOSTATS_PROMPT, CODING_PROMPT, DIAGNOSTIC_PROMPT
from app.agents.state import BiostatisticsOutput, CodingOutput, ResearchState
from app.services.llm import get_chat_model
from app.services.memory import trim_messages


# ---------------------------------------------------------------------------
# 1. BiostatisticsAgent -- power/sample size, clarification loop
# ---------------------------------------------------------------------------

async def biostatistics_node(state: ResearchState) -> dict:
    """Guide through statistical lifecycle: power analysis, study design, interpretation.

    If the agent sets ``diagnostic_query``, the diagnostic tool is called automatically
    and its recommendation is appended to the response.
    """

    llm = get_chat_model("biostatistics").with_structured_output(BiostatisticsOutput)

    user_text = build_input_text(state)
    messages = [
        SystemMessage(content=BIOSTATS_PROMPT),
        *trim_messages(state["messages"]),
        HumanMessage(content=user_text),
    ]

    result: BiostatisticsOutput = await llm.ainvoke(messages)

    response_text = result.direct_response_to_user

    # Auto-call diagnostic tool if the agent requested it
    if result.diagnostic_query:
        diagnostic_result = await run_diagnostic(result.diagnostic_query)
        response_text = (
            f"{response_text}\n\n"
            f"### Diagnostic Tool Recommendation\n\n{diagnostic_result}"
        )

    return {
        "messages": [AIMessage(content=response_text)],
        "need_info": result.need_info,
        "forwarded_message": result.forwarded_message,
    }


# ---------------------------------------------------------------------------
# 2. DiagnosticTool -- statistical test selection (used as tool by biostats)
# ---------------------------------------------------------------------------

async def run_diagnostic(query: str) -> str:
    """Run the diagnostic tool to recommend a statistical test.

    Called as a tool by the biostatistics agent, not as a standalone graph node.
    """

    llm = get_chat_model("diagnostic")

    messages = [
        SystemMessage(content=DIAGNOSTIC_PROMPT),
        HumanMessage(content=query),
    ]

    response = await llm.ainvoke(messages)
    return response.content


# ---------------------------------------------------------------------------
# 3. CodingAgent -- Python/R/STATA code generation + routing
# ---------------------------------------------------------------------------

async def coding_node(state: ResearchState) -> dict:
    """Generate statistical code and decide next step.

    This node now also handles routing (previously done by secretary + routing nodes).
    """

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
        "agent_to_route_to": result.agent_to_route_to,
        "current_phase": result.agent_to_route_to or "biostatistics",
        "forwarded_message": result.forwarded_message,
    }
