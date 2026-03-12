"""Integration tests for the LangGraph StateGraph construction."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from langchain_core.messages import HumanMessage

from app.agents.graph import build_graph
from app.agents.state import (
    GapSearchOutput,
    GapSummarizeOutput,
    OrchestratorOutput,
)
from app.services.tavily import SearchResult
from tests.conftest import base_state, make_mock_structured_llm


class TestGraphConstruction:
    def test_graph_compiles(self):
        graph = build_graph()
        compiled = graph.compile()
        assert compiled is not None

    def test_graph_has_expected_nodes(self):
        graph = build_graph()
        node_names = set(graph.nodes.keys())
        expected = {
            "entry_router",
            "orchestrator",
            "gap_search",
            "gap_summarize",
            "methodology",
            "biostatistics",
            "coding",
        }
        assert expected.issubset(node_names)


class TestGraphFlow:
    @pytest.mark.asyncio
    async def test_orchestrator_to_gap_search_to_gap_summarize(self):
        """Full flow: user message -> orchestrator -> gap_search -> gap_summarize -> END."""
        orch_output = OrchestratorOutput(
            direct_response_to_user="Routing to research gap.",
            agent_to_route_to="research_gap",
            forwarded_message="search for diabetes gaps",
        )
        gap_search_output = GapSearchOutput(terms=["diabetes RCT"])
        gap_summarize_output = GapSummarizeOutput(
            direct_response_to_user="Here are the research gaps.",
        )

        mock_search_results = [
            SearchResult(url="https://pubmed.ncbi.nlm.nih.gov/1", title="Study", content="content", score=0.9),
        ]

        orch_mock = make_mock_structured_llm(orch_output)
        gap_search_mock = make_mock_structured_llm(gap_search_output)
        gap_summarize_mock = make_mock_structured_llm(gap_summarize_output)

        def model_factory(agent_name, schema):
            return {
                "orchestrator": orch_mock,
                "gap_search": gap_search_mock,
                "gap_summarize": gap_summarize_mock,
            }[agent_name]

        with (
            patch("app.agents.orchestrator.get_structured_model", side_effect=model_factory),
            patch("app.agents.research_gap.get_structured_model", side_effect=model_factory),
            patch("app.agents.research_gap.search", AsyncMock(return_value=mock_search_results)),
        ):
            graph = build_graph()
            compiled = graph.compile()

            initial_state = base_state(
                messages=[HumanMessage(content="Find research gaps in diabetes treatment")],
            )

            result = await compiled.ainvoke(initial_state)

        # Should have messages from orchestrator, gap_search progress, and gap_summarize
        assert len(result["messages"]) >= 3
        assert result["current_phase"] == "research_gap"
        assert result["search_count"] == 1

    @pytest.mark.asyncio
    async def test_followup_skips_gap_search(self):
        """Follow-up message in research_gap phase skips gap_search, goes to gap_summarize."""
        gap_summarize_output = GapSummarizeOutput(
            direct_response_to_user="Explaining the third gap.",
        )
        gap_summarize_mock = make_mock_structured_llm(gap_summarize_output)

        def model_factory(agent_name, schema):
            if agent_name == "gap_summarize":
                return gap_summarize_mock
            raise AssertionError(f"Unexpected model request: {agent_name}")

        with (
            patch("app.agents.research_gap.get_structured_model", side_effect=model_factory),
        ):
            graph = build_graph()
            compiled = graph.compile()

            # Simulate follow-up: phase is already research_gap, search_count=0
            # (entry_router resets it), but existing results from previous turn
            initial_state = base_state(
                messages=[HumanMessage(content="explain the third gap")],
                current_phase="research_gap",
                search_results=[
                    {"title": "Study A", "url": "https://a.com", "content": "a", "score": 0.9},
                ],
            )

            result = await compiled.ainvoke(initial_state)

        # gap_search was NOT called (model_factory would raise for any agent besides gap_summarize)
        assert "Explaining the third gap" in result["messages"][-1].content
        # search_count stays 0 because gap_search was skipped
        assert result["search_count"] == 0
