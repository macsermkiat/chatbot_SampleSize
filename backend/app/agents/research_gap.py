"""Research Gap phase nodes: search, summarize, secretary."""

from __future__ import annotations

import json

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from app.agents.prompts import (
    GAP_SEARCH_PROMPT,
    GAP_SECRETARY_PROMPT,
    GAP_SUMMARIZE_PROMPT,
)
from app.agents.state import (
    GapSearchOutput,
    GapSummarizeOutput,
    ResearchState,
    SecretaryOutput,
)
from app.services.llm import get_chat_model
from app.services.memory import trim_messages
from app.services.tavily import SearchResult, search


# ---------------------------------------------------------------------------
# 1. ResearchGapAgentSearch -- generates 3-5 Tavily search terms
# ---------------------------------------------------------------------------

async def gap_search_node(state: ResearchState) -> dict:
    """Generate search terms and execute Tavily searches."""

    llm = get_chat_model("gap_search").with_structured_output(GapSearchOutput)

    # Build the prompt text matching the n8n template
    user_text = _build_input_text(state)
    messages = [
        SystemMessage(content=GAP_SEARCH_PROMPT),
        HumanMessage(content=user_text),
    ]

    result: GapSearchOutput = await llm.ainvoke(messages)

    queries = list(result.terms)
    search_results: list[SearchResult] = await search(queries)

    # Emit a progress message
    term_list = "\n".join(f"  {i+1}. {q}" for i, q in enumerate(queries))
    progress_msg = f"Searching with {len(queries)} terms:\n{term_list}"

    return {
        "messages": [AIMessage(content=progress_msg)],
        "search_results": [
            {"url": r.url, "title": r.title, "content": r.content, "score": r.score}
            for r in search_results
        ],
    }


# ---------------------------------------------------------------------------
# 2. ResearchGapSummarize -- appraises evidence, classifies gaps
# ---------------------------------------------------------------------------

async def gap_summarize_node(state: ResearchState) -> dict:
    """Summarize search results, classify gaps, and draft PICOTS question."""

    llm = get_chat_model("gap_summarize").with_structured_output(GapSummarizeOutput)

    # Format search results into the prompt (matches n8n template)
    search_block = _format_search_results(state.get("search_results", []))
    user_text = _build_input_text(state)
    combined = f"{user_text}\n\nSearch Result: {search_block}"

    messages = [
        SystemMessage(content=GAP_SUMMARIZE_PROMPT),
        HumanMessage(content=combined),
    ]

    result: GapSummarizeOutput = await llm.ainvoke(messages)

    return {
        "messages": [AIMessage(content=result.direct_response_to_user)],
        "agent_to_route_to": result.agent_to_route_to,
        "forwarded_message": result.forwarded_message,
    }


# ---------------------------------------------------------------------------
# 3. ResearchGapSecretary -- summarizes and routes
# ---------------------------------------------------------------------------

async def gap_secretary_node(state: ResearchState) -> dict:
    """Summarize the gap phase output and wait for user input.

    The secretary summarizes what the search+summarize pipeline produced.
    After the first pass it should always return to the user (agent_to_route_to="")
    rather than looping back into gap_search -- the user decides next steps.
    """

    llm = get_chat_model("gap_secretary").with_structured_output(SecretaryOutput)

    # Collect the last AI messages as the agents' output to summarize
    agent_output_parts = []
    for msg in reversed(state.get("messages", [])):
        if getattr(msg, "type", None) == "ai":
            agent_output_parts.append(msg.content)
        elif getattr(msg, "type", None) == "human":
            break
    agent_output = "\n\n".join(reversed(agent_output_parts))

    messages = [
        SystemMessage(content=GAP_SECRETARY_PROMPT),
        HumanMessage(
            content=(
                f"Agent output to summarize:\n{agent_output}\n\n"
                "The user has NOT responded yet. Summarize the findings and "
                "ask the user what they want to do next. Set agent_to_route_to "
                "to empty string."
            )
        ),
    ]

    result: SecretaryOutput = await llm.ainvoke(messages)

    return {
        "messages": [AIMessage(content=result.direct_response_to_user)],
        # Force end-of-turn: let the user decide the next step
        "agent_to_route_to": "",
        "forwarded_message": result.forwarded_message,
    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _build_input_text(state: ResearchState) -> str:
    """Construct the input text block matching the n8n template variables."""
    forwarded = state.get("forwarded_message", "") or "-"
    # Get the latest user message
    user_msg = "-"
    for msg in reversed(state.get("messages", [])):
        if getattr(msg, "type", None) == "human":
            user_msg = msg.content
            break
    return f"Query from other agent: {forwarded}\n\nUser response: {user_msg}"


def _format_search_results(results: list[dict]) -> str:
    """Format search results into the text block the n8n template uses."""
    if not results:
        return "No search results available."
    lines = []
    for i, r in enumerate(results, 1):
        lines.append(f"{i}. {r.get('title', '')}\n{r.get('url', '')}\n{r.get('content', '')}")
    return "\n\n".join(lines)
