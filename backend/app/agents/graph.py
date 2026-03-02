"""LangGraph StateGraph -- wires all agent nodes with conditional routing.

Architecture (modernized):

    User -> entry_router (pure Python, zero LLM) -> [Orchestrator | phase node]
                                                          |
                     +------------------------------------+--------------------+
                     |                                    |                    |
               ResearchGap                          Methodology         Biostatistics
             search -> summarize                       agent            agent -> coding
                     |                                    |                    |
             [conditional: route or END]        [conditional: route    [conditional: route
                                                  or END]               or END]

Each phase's main agent now handles routing directly (no secretary layer).
"""

from __future__ import annotations

import logging
import re

from langgraph.graph import END, StateGraph

from app.agents.biostatistics import (
    _is_code_request,
    biostatistics_node,
    coding_node,
)
from app.agents.helpers import get_latest_user_message
from app.agents.methodology import methodology_node
from app.agents.orchestrator import orchestrator_node
from app.agents.research_gap import gap_search_node, gap_summarize_node
from app.agents.state import ResearchState

_logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Phase entry-point mapping
# ---------------------------------------------------------------------------

_PHASE_ENTRY = {
    "research_gap": "gap_search",
    "methodology": "methodology",
    "biostatistics": "biostatistics",
}

# Follow-up routing: user messages within an active phase skip the search
# step and go to the conversational node instead.
_PHASE_FOLLOWUP = {
    "research_gap": "gap_summarize",
    "methodology": "methodology",
    "biostatistics": "biostatistics",
}

# Keywords that signal the user wants to switch phases
_PHASE_SWITCH_PATTERNS = re.compile(
    r"\b(switch|change|go\s+to|move\s+to|start\s+over|new\s+topic|different\s+topic)\b",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# Entry router (pure Python -- zero LLM calls)
# ---------------------------------------------------------------------------

def _entry_router(state: ResearchState) -> dict:
    """Decide whether to route to orchestrator or directly to current phase.

    Resets ``search_count`` so the per-turn loop guard starts fresh.
    The actual routing decision is handled by ``_route_from_entry``
    via conditional edges.
    """
    return {"search_count": 0}


def _route_from_entry(state: ResearchState) -> str:
    """Conditional edge after entry_router: skip orchestrator when possible."""
    phase = state.get("current_phase", "orchestrator")

    # First message or orchestrator phase -> always go through orchestrator
    if phase == "orchestrator":
        return "orchestrator"

    # If user explicitly wants to switch phases, go through orchestrator
    last_msg = get_latest_user_message(state)
    if _PHASE_SWITCH_PATTERNS.search(last_msg):
        return "orchestrator"

    # Shortcut: if user requests code and we have pending code, go to coding
    if (
        phase == "biostatistics"
        and state.get("has_pending_code")
        and _is_code_request(last_msg)
    ):
        return "coding"

    # Route to conversational node (not search) for follow-up messages
    return _PHASE_FOLLOWUP.get(phase, "orchestrator")


# ---------------------------------------------------------------------------
# Routing functions (conditional edges from phase nodes)
# ---------------------------------------------------------------------------

def _route_from_orchestrator(state: ResearchState) -> str:
    """After orchestrator: route to a specialist or wait for user clarification."""
    if state.get("needs_clarification"):
        return END

    target = state.get("agent_to_route_to", "")
    return _PHASE_ENTRY.get(target, END)


def _route_from_gap_summarize(state: ResearchState) -> str:
    """After gap summarize: route to another phase or end (wait for user).

    Loop guard: only allows one search per graph invocation.  If
    ``search_count >= 1`` and the LLM requests another search, we END
    instead -- the next user message will re-enter via entry_router.
    """
    target = state.get("agent_to_route_to", "")
    if not target:
        return END
    if target == "research_gap":
        if state.get("search_count", 0) >= 1:
            _logger.info("Search loop capped (search_count=%d), ending turn", state.get("search_count", 0))
            return END
        return "gap_search"
    mapped = _PHASE_ENTRY.get(target)
    if mapped is None:
        _logger.warning("Unknown agent_to_route_to from gap_summarize: %r", target)
        return END
    return mapped


def _route_from_methodology(state: ResearchState) -> str:
    """After methodology: route to another phase or end (wait for user)."""
    target = state.get("agent_to_route_to", "")
    if not target:
        return END
    mapped = _PHASE_ENTRY.get(target)
    if mapped is None:
        _logger.warning("Unknown agent_to_route_to from methodology: %r", target)
        return END
    return mapped


def _route_from_biostats(state: ResearchState) -> str:
    """After biostatistics agent: if need_info=true, wait for user.

    Only advances to coding when the agent has a forwarded instruction.
    """
    if state.get("need_info"):
        return END
    if state.get("forwarded_message", ""):
        return "coding"
    return END


def _route_from_coding(state: ResearchState) -> str:
    """After coding: route to another phase or end (wait for user)."""
    target = state.get("agent_to_route_to", "")
    if not target:
        return END
    mapped = _PHASE_ENTRY.get(target)
    if mapped is None:
        _logger.warning("Unknown agent_to_route_to from coding: %r", target)
        return END
    return mapped


# ---------------------------------------------------------------------------
# Graph construction
# ---------------------------------------------------------------------------

def build_graph() -> StateGraph:
    """Construct and return the (uncompiled) research assistant StateGraph."""

    graph = StateGraph(ResearchState)

    # --- Add nodes (7 + 1 pure-Python router) ---
    graph.add_node("entry_router", _entry_router)
    graph.add_node("orchestrator", orchestrator_node)

    # Research Gap phase
    graph.add_node("gap_search", gap_search_node)
    graph.add_node("gap_summarize", gap_summarize_node)

    # Methodology phase
    graph.add_node("methodology", methodology_node)

    # Biostatistics phase
    graph.add_node("biostatistics", biostatistics_node)
    graph.add_node("coding", coding_node)

    # --- Entry point ---
    graph.set_entry_point("entry_router")

    # --- Entry router edges ---
    graph.add_conditional_edges(
        "entry_router",
        _route_from_entry,
        {
            "orchestrator": "orchestrator",
            "gap_search": "gap_search",
            "gap_summarize": "gap_summarize",
            "methodology": "methodology",
            "biostatistics": "biostatistics",
            "coding": "coding",
        },
    )

    # --- Edges from orchestrator ---
    graph.add_conditional_edges(
        "orchestrator",
        _route_from_orchestrator,
        {
            "gap_search": "gap_search",
            "methodology": "methodology",
            "biostatistics": "biostatistics",
            END: END,
        },
    )

    # --- Research Gap edges ---
    graph.add_edge("gap_search", "gap_summarize")
    graph.add_conditional_edges(
        "gap_summarize",
        _route_from_gap_summarize,
        {
            "gap_search": "gap_search",
            "methodology": "methodology",
            "biostatistics": "biostatistics",
            END: END,
        },
    )

    # --- Methodology edges ---
    graph.add_conditional_edges(
        "methodology",
        _route_from_methodology,
        {
            "gap_search": "gap_search",
            "biostatistics": "biostatistics",
            END: END,
        },
    )

    # --- Biostatistics edges ---
    graph.add_conditional_edges(
        "biostatistics",
        _route_from_biostats,
        {
            "coding": "coding",
            END: END,
        },
    )
    graph.add_conditional_edges(
        "coding",
        _route_from_coding,
        {
            "gap_search": "gap_search",
            "methodology": "methodology",
            "biostatistics": "biostatistics",
            END: END,
        },
    )

    return graph
