"""Tests for routing logic in app.agents.graph -- pure Python, no LLM calls."""

from langchain_core.messages import HumanMessage
from langgraph.graph import END

from app.agents.graph import (
    _entry_router,
    _route_from_biostats,
    _route_from_coding,
    _route_from_entry,
    _route_from_gap_summarize,
    _route_from_methodology,
    _route_from_orchestrator,
)
from tests.conftest import base_state


# ---------------------------------------------------------------------------
# _entry_router
# ---------------------------------------------------------------------------

class TestEntryRouter:
    def test_resets_search_count(self):
        state = base_state(search_count=5)
        result = _entry_router(state)
        assert result["search_count"] == 0


# ---------------------------------------------------------------------------
# _route_from_entry
# ---------------------------------------------------------------------------

class TestRouteFromEntry:
    def test_orchestrator_phase_routes_to_orchestrator(self):
        state = base_state(current_phase="orchestrator")
        assert _route_from_entry(state) == "orchestrator"

    def test_research_gap_followup_routes_to_gap_summarize(self):
        state = base_state(current_phase="research_gap")
        assert _route_from_entry(state) == "gap_summarize"

    def test_methodology_followup_routes_to_methodology(self):
        state = base_state(current_phase="methodology")
        assert _route_from_entry(state) == "methodology"

    def test_biostatistics_followup_routes_to_biostatistics(self):
        state = base_state(current_phase="biostatistics")
        assert _route_from_entry(state) == "biostatistics"

    def test_switch_keyword_routes_to_orchestrator(self):
        state = base_state(
            current_phase="research_gap",
            messages=[HumanMessage(content="switch to methodology")],
        )
        assert _route_from_entry(state) == "orchestrator"

    def test_go_to_keyword_routes_to_orchestrator(self):
        state = base_state(
            current_phase="methodology",
            messages=[HumanMessage(content="go to biostatistics")],
        )
        assert _route_from_entry(state) == "orchestrator"

    def test_unknown_phase_falls_back_to_orchestrator(self):
        state = base_state(current_phase="unknown_phase")
        assert _route_from_entry(state) == "orchestrator"


# ---------------------------------------------------------------------------
# _route_from_orchestrator
# ---------------------------------------------------------------------------

class TestRouteFromOrchestrator:
    def test_clarification_ends(self):
        state = base_state(needs_clarification=True)
        assert _route_from_orchestrator(state) == END

    def test_routes_to_research_gap(self):
        state = base_state(agent_to_route_to="research_gap")
        assert _route_from_orchestrator(state) == "gap_search"

    def test_routes_to_methodology(self):
        state = base_state(agent_to_route_to="methodology")
        assert _route_from_orchestrator(state) == "methodology"

    def test_routes_to_biostatistics(self):
        state = base_state(agent_to_route_to="biostatistics")
        assert _route_from_orchestrator(state) == "biostatistics"

    def test_empty_target_ends(self):
        state = base_state(agent_to_route_to="")
        assert _route_from_orchestrator(state) == END


# ---------------------------------------------------------------------------
# _route_from_gap_summarize
# ---------------------------------------------------------------------------

class TestRouteFromGapSummarize:
    def test_empty_target_ends(self):
        state = base_state(agent_to_route_to="")
        assert _route_from_gap_summarize(state) == END

    def test_loop_cap_prevents_second_search(self):
        state = base_state(agent_to_route_to="research_gap", search_count=1)
        assert _route_from_gap_summarize(state) == END

    def test_allows_search_when_count_zero(self):
        state = base_state(agent_to_route_to="research_gap", search_count=0)
        assert _route_from_gap_summarize(state) == "gap_search"

    def test_routes_to_methodology(self):
        state = base_state(agent_to_route_to="methodology")
        assert _route_from_gap_summarize(state) == "methodology"

    def test_routes_to_biostatistics(self):
        state = base_state(agent_to_route_to="biostatistics")
        assert _route_from_gap_summarize(state) == "biostatistics"

    def test_unknown_target_ends(self):
        state = base_state(agent_to_route_to="nonexistent")
        assert _route_from_gap_summarize(state) == END


# ---------------------------------------------------------------------------
# _route_from_methodology
# ---------------------------------------------------------------------------

class TestRouteFromMethodology:
    def test_empty_target_ends(self):
        state = base_state(agent_to_route_to="")
        assert _route_from_methodology(state) == END

    def test_routes_to_biostatistics(self):
        state = base_state(agent_to_route_to="biostatistics")
        assert _route_from_methodology(state) == "biostatistics"

    def test_unknown_target_ends(self):
        state = base_state(agent_to_route_to="unknown")
        assert _route_from_methodology(state) == END


# ---------------------------------------------------------------------------
# _route_from_biostats
# ---------------------------------------------------------------------------

class TestRouteFromBiostats:
    def test_need_info_ends(self):
        state = base_state(need_info=True)
        assert _route_from_biostats(state) == END

    def test_forwarded_message_routes_to_coding(self):
        state = base_state(need_info=False, forwarded_message="do stats")
        assert _route_from_biostats(state) == "coding"

    def test_no_forwarded_message_ends(self):
        state = base_state(need_info=False, forwarded_message="")
        assert _route_from_biostats(state) == END


# ---------------------------------------------------------------------------
# _route_from_coding
# ---------------------------------------------------------------------------

class TestRouteFromCoding:
    def test_empty_target_ends(self):
        state = base_state(agent_to_route_to="")
        assert _route_from_coding(state) == END

    def test_routes_to_research_gap(self):
        state = base_state(agent_to_route_to="research_gap")
        assert _route_from_coding(state) == "gap_search"

    def test_routes_to_methodology(self):
        state = base_state(agent_to_route_to="methodology")
        assert _route_from_coding(state) == "methodology"

    def test_unknown_target_ends(self):
        state = base_state(agent_to_route_to="unknown")
        assert _route_from_coding(state) == END
