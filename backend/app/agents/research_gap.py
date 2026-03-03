"""Research Gap phase nodes: search and summarize.

The secretary node has been removed -- the summarize node now handles
routing decisions directly, reducing one LLM call per phase execution.
"""

from __future__ import annotations

from urllib.parse import urlparse

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from app.agents.helpers import build_input_text
from app.agents.prompt_composer import get_prompt
from app.agents.prompts import GAP_SEARCH_PROMPT, GAP_SUMMARIZE_PROMPT
from app.agents.state import GapSearchOutput, GapSummarizeOutput, ResearchState
from app.services.llm import get_chat_model, get_structured_model
from app.services.memory import trim_messages
from app.services.tavily import SearchResult, search


# ---------------------------------------------------------------------------
# 1. ResearchGapAgentSearch -- generates 3-5 Tavily search terms
# ---------------------------------------------------------------------------

async def gap_search_node(state: ResearchState) -> dict:
    """Generate search terms and execute Tavily searches."""

    llm = get_structured_model("gap_search", GapSearchOutput)

    expertise = state.get("expertise_level", "advanced")
    user_text = build_input_text(state)
    messages = [
        SystemMessage(content=get_prompt(GAP_SEARCH_PROMPT, expertise, "gap_search")),
        *trim_messages(state["messages"]),
        HumanMessage(content=user_text),
    ]

    result: GapSearchOutput = await llm.ainvoke(messages)

    queries = list(result.terms)
    search_results: list[SearchResult] = await search(queries)

    progress_msg = _format_progress(queries, search_results, expertise)

    return {
        "messages": [AIMessage(content=progress_msg)],
        "search_results": [
            {"url": r.url, "title": r.title, "content": r.content, "score": r.score}
            for r in search_results
        ],
        # Increment loop guard counter
        "search_count": state.get("search_count", 0) + 1,
        # Clear stale routing state so gap_summarize starts with a clean slate
        "agent_to_route_to": "",
        "forwarded_message": "",
    }


# ---------------------------------------------------------------------------
# 2. ResearchGapSummarize -- appraises evidence, classifies gaps, routes
# ---------------------------------------------------------------------------

async def gap_summarize_node(state: ResearchState) -> dict:
    """Summarize search results, classify gaps, and decide next step.

    This node now also handles routing (previously done by the secretary).
    """

    llm = get_structured_model("gap_summarize", GapSummarizeOutput)

    raw_results = state.get("search_results", [])
    search_block = _format_search_results(raw_results)
    is_fresh = state.get("search_count", 0) >= 1

    if is_fresh or not raw_results:
        results_section = f"Search Results:\n{search_block}"
    else:
        results_section = (
            "Previous Search Results (from a prior query -- use these if the user "
            "is asking about them, otherwise set agent_to_route_to='research_gap' "
            "to trigger a fresh search):\n" + search_block
        )

    user_text = build_input_text(state)
    combined = f"{user_text}\n\n{results_section}"

    expertise = state.get("expertise_level", "advanced")
    messages = [
        SystemMessage(content=get_prompt(GAP_SUMMARIZE_PROMPT, expertise, "gap_summarize")),
        *trim_messages(state["messages"]),
        HumanMessage(content=combined),
    ]

    result: GapSummarizeOutput = await llm.ainvoke(messages)

    return {
        "messages": [AIMessage(content=result.direct_response_to_user)],
        "needs_clarification": result.needs_clarification,
        "agent_to_route_to": "" if result.needs_clarification else result.agent_to_route_to,
        "current_phase": result.agent_to_route_to or "research_gap",
        "forwarded_message": result.forwarded_message,
    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _format_search_results(results: list[dict]) -> str:
    """Format search results for the LLM prompt (includes URLs for citation)."""
    if not results:
        return "No search results available."
    lines: list[str] = []
    for i, r in enumerate(results, 1):
        title = r.get("title", "Untitled")
        url = r.get("url", "")
        content = r.get("content", "")
        score = r.get("score", 0.0)
        lines.append(
            f"{i}. **{title}**\n"
            f"   URL: {url}\n"
            f"   Relevance: {score:.2f}\n"
            f"   {content}"
        )
    return "\n\n".join(lines)


def _format_progress(
    queries: list[str],
    results: list[SearchResult],
    expertise_level: str = "advanced",
) -> str:
    """Build a user-friendly progress message with clickable links.

    In simple mode: hides raw search terms and limits to top 5 sources
    with no raw snippets. In advanced mode: shows full detail.
    """
    parts: list[str] = []
    is_simple = expertise_level == "simple"

    if is_simple:
        # Simple mode: hide MeSH/boolean search terms from user
        parts.append(f"**Searching for relevant studies...** "
                     f"(checked {len(queries)} search strategies)\n")
    else:
        parts.append("## Search Terms\n")
        for i, q in enumerate(queries, 1):
            parts.append(f"{i}. {q}")
        parts.append("")

    if not results:
        parts.append("No results found. Try refining your topic.\n")
        return "\n".join(parts)

    # Simple mode: show top 5 titles only, no raw snippets
    display_results = results[:5] if is_simple else results
    parts.append(f"**Found {len(results)} sources.** "
                 f"Here are the most relevant:\n")

    for i, r in enumerate(display_results, 1):
        title = r.title or "Untitled"
        link = f"[{title}]({r.url})" if r.url else title
        domain = _extract_domain(r.url)
        domain_badge = f" -- *{domain}*" if domain else ""
        parts.append(f"**{i}.** {link}{domain_badge}")

        if not is_simple:
            content = r.content or ""
            snippet = (content[:180] + "...") if len(content) > 180 else content
            parts.append(f"> {snippet}\n")
        else:
            parts.append("")

    parts.append("---")
    parts.append("*Analyzing these sources now...*")

    return "\n".join(parts)


def _extract_domain(url: str) -> str:
    """Extract a readable domain name from a URL."""
    if not url:
        return ""
    try:
        domain = urlparse(url).hostname or ""
    except Exception:
        return ""
    if domain.startswith("www."):
        domain = domain[4:]
    return domain
