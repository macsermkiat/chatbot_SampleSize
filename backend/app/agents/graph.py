"""LangGraph StateGraph -- wires all agent nodes with conditional routing.

Architecture mirrors the n8n workflow:

    User -> Orchestrator -> [ResearchGap | Methodology | Biostatistics]
                                    |              |              |
                              search->summarize  agent        agent->coding
                                    |              |              |
                               secretary       secretary     secretary->routing
                                    |              |              |
                          [route back to orchestrator or stay in phase]

Each phase has internal sub-steps that execute sequentially, then a secretary
node that decides whether to stay in the current phase or route elsewhere.
"""

from __future__ import annotations

from langgraph.graph import END, StateGraph

from app.agents.biostatistics import (
    biostatistics_node,
    biostats_routing_node,
    biostats_secretary_node,
    coding_node,
)
from app.agents.methodology import methodology_node, methodology_secretary_node
from app.agents.orchestrator import orchestrator_node
from app.agents.research_gap import (
    gap_search_node,
    gap_secretary_node,
    gap_summarize_node,
)
from app.agents.state import ResearchState


# ---------------------------------------------------------------------------
# Routing functions (conditional edges)
# ---------------------------------------------------------------------------

_ROUTE_MAP = {
    "ResearchGapAgent": "gap_search",
    "MethodologyAgent": "methodology",
    "BiostatisticsAgent": "biostatistics",
}


def _route_from_orchestrator(state: ResearchState) -> str:
    """After orchestrator: route to a specialist or wait for user clarification."""
    if state.get("needs_clarification"):
        return END

    target = state.get("agent_to_route_to", "")
    return _ROUTE_MAP.get(target, END)


def _route_from_gap_secretary(state: ResearchState) -> str:
    """After gap secretary: continue in gap, route elsewhere, or end."""
    target = state.get("agent_to_route_to", "")
    if not target:
        return END  # stay in conversation (user will send next message)
    if target == "ResearchGapAgent":
        return "gap_search"
    return _ROUTE_MAP.get(target, "orchestrator")


def _route_from_methodology_secretary(state: ResearchState) -> str:
    """After methodology secretary: continue, route elsewhere, or end."""
    target = state.get("agent_to_route_to", "")
    if not target:
        return END
    return _ROUTE_MAP.get(target, "orchestrator")


def _route_from_biostats(state: ResearchState) -> str:
    """After biostatistics agent: if need_info=true, wait for user; else go to coding."""
    if state.get("need_info"):
        return END  # user needs to provide more info
    return "coding"


def _route_from_biostats_routing(state: ResearchState) -> str:
    """After biostats routing: route to another phase or end."""
    target = state.get("agent_to_route_to", "")
    if not target:
        return END
    return _ROUTE_MAP.get(target, "orchestrator")


# ---------------------------------------------------------------------------
# Graph construction
# ---------------------------------------------------------------------------

def build_graph() -> StateGraph:
    """Construct and return the (uncompiled) research assistant StateGraph."""

    graph = StateGraph(ResearchState)

    # --- Add nodes ---
    graph.add_node("orchestrator", orchestrator_node)

    # Research Gap phase
    graph.add_node("gap_search", gap_search_node)
    graph.add_node("gap_summarize", gap_summarize_node)
    graph.add_node("gap_secretary", gap_secretary_node)

    # Methodology phase
    graph.add_node("methodology", methodology_node)
    graph.add_node("methodology_secretary", methodology_secretary_node)

    # Biostatistics phase
    graph.add_node("biostatistics", biostatistics_node)
    graph.add_node("coding", coding_node)
    graph.add_node("biostats_secretary", biostats_secretary_node)
    graph.add_node("biostats_routing", biostats_routing_node)

    # --- Entry point ---
    graph.set_entry_point("orchestrator")

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
    graph.add_edge("gap_summarize", "gap_secretary")
    graph.add_conditional_edges(
        "gap_secretary",
        _route_from_gap_secretary,
        {
            "gap_search": "gap_search",
            "methodology": "methodology",
            "biostatistics": "biostatistics",
            "orchestrator": "orchestrator",
            END: END,
        },
    )

    # --- Methodology edges ---
    graph.add_edge("methodology", "methodology_secretary")
    graph.add_conditional_edges(
        "methodology_secretary",
        _route_from_methodology_secretary,
        {
            "gap_search": "gap_search",
            "biostatistics": "biostatistics",
            "orchestrator": "orchestrator",
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
    graph.add_edge("coding", "biostats_secretary")
    graph.add_edge("biostats_secretary", "biostats_routing")
    graph.add_conditional_edges(
        "biostats_routing",
        _route_from_biostats_routing,
        {
            "gap_search": "gap_search",
            "methodology": "methodology",
            "orchestrator": "orchestrator",
            END: END,
        },
    )

    return graph
