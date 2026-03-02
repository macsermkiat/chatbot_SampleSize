"""Tests for agent nodes with mocked LLM calls."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

from langchain_core.messages import HumanMessage

from app.agents.biostatistics import biostatistics_node, coding_node
from app.agents.methodology import methodology_node
from app.agents.orchestrator import orchestrator_node
from app.agents.research_gap import gap_search_node, gap_summarize_node
from app.agents.state import (
    BiostatisticsOutput,
    CodingOutput,
    GapSearchOutput,
    GapSummarizeOutput,
    MethodologyOutput,
    OrchestratorOutput,
)
from app.services.code_executor import ExecutionResult
from app.services.tavily import SearchResult
from tests.conftest import base_state, make_mock_llm


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------

class TestOrchestratorNode:
    async def test_routes_to_research_gap(self, patch_get_chat_model):
        output = OrchestratorOutput(
            direct_response_to_user="Routing to research gap.",
            agent_to_route_to="research_gap",
            forwarded_message="analyze diabetes",
        )
        patch_get_chat_model("app.agents.orchestrator", output)
        state = base_state()

        result = await orchestrator_node(state)

        assert result["current_phase"] == "research_gap"
        assert result["agent_to_route_to"] == "research_gap"
        assert "Routing" in result["messages"][0].content

    async def test_needs_clarification(self, patch_get_chat_model):
        output = OrchestratorOutput(
            direct_response_to_user="Can you clarify?",
            needs_clarification=True,
        )
        patch_get_chat_model("app.agents.orchestrator", output)
        state = base_state()

        result = await orchestrator_node(state)

        assert result["needs_clarification"] is True
        assert result["agent_to_route_to"] == ""


# ---------------------------------------------------------------------------
# GapSearch
# ---------------------------------------------------------------------------

class TestGapSearchNode:
    async def test_returns_search_results(self, patch_get_chat_model, patch_tavily_search):
        output = GapSearchOutput(terms=["diabetes RCT", "HbA1c trials"])
        patch_get_chat_model("app.agents.research_gap", output)
        mock_results = [
            SearchResult(url="https://pubmed.ncbi.nlm.nih.gov/1", title="Study 1", content="content1", score=0.9),
            SearchResult(url="https://pubmed.ncbi.nlm.nih.gov/2", title="Study 2", content="content2", score=0.8),
        ]
        patch_tavily_search(mock_results)

        state = base_state()

        result = await gap_search_node(state)

        assert len(result["search_results"]) == 2
        assert result["search_count"] == 1
        assert result["agent_to_route_to"] == ""

    async def test_increments_count(self, patch_get_chat_model, patch_tavily_search):
        output = GapSearchOutput(terms=["term"])
        patch_get_chat_model("app.agents.research_gap", output)
        patch_tavily_search([])

        state = base_state(search_count=2)

        result = await gap_search_node(state)

        assert result["search_count"] == 3


# ---------------------------------------------------------------------------
# GapSummarize
# ---------------------------------------------------------------------------

class TestGapSummarizeNode:
    async def test_fresh_results_label(self, patch_get_chat_model):
        output = GapSummarizeOutput(direct_response_to_user="Here is the summary.")
        mock = patch_get_chat_model("app.agents.research_gap", output)
        state = base_state(
            search_count=1,
            search_results=[{"title": "Study", "url": "https://a.com", "content": "c", "score": 0.9}],
        )

        await gap_summarize_node(state)

        # Verify the prompt sent to the LLM contains "Search Results:" (fresh label)
        call_args = mock.with_structured_output.return_value.ainvoke.call_args
        sent_messages = call_args[0][0]
        human_msg = sent_messages[-1].content
        assert "Search Results:" in human_msg
        assert "Previous Search Results" not in human_msg

    async def test_stale_results_label(self, patch_get_chat_model):
        output = GapSummarizeOutput(direct_response_to_user="Summary of stale.")
        mock = patch_get_chat_model("app.agents.research_gap", output)
        state = base_state(
            search_count=0,
            search_results=[{"title": "Old Study", "url": "https://b.com", "content": "old", "score": 0.7}],
        )

        await gap_summarize_node(state)

        call_args = mock.with_structured_output.return_value.ainvoke.call_args
        sent_messages = call_args[0][0]
        human_msg = sent_messages[-1].content
        assert "Previous Search Results" in human_msg

    async def test_no_results_gets_fresh_label(self, patch_get_chat_model):
        output = GapSummarizeOutput(direct_response_to_user="No results.")
        mock = patch_get_chat_model("app.agents.research_gap", output)
        state = base_state(search_count=0, search_results=[])

        await gap_summarize_node(state)

        call_args = mock.with_structured_output.return_value.ainvoke.call_args
        sent_messages = call_args[0][0]
        human_msg = sent_messages[-1].content
        assert "Search Results:" in human_msg
        assert "Previous Search Results" not in human_msg

    async def test_routes_to_methodology(self, patch_get_chat_model):
        output = GapSummarizeOutput(
            direct_response_to_user="Gaps identified.",
            agent_to_route_to="methodology",
            forwarded_message="proceed to study design",
        )
        patch_get_chat_model("app.agents.research_gap", output)
        state = base_state(search_count=1, search_results=[])

        result = await gap_summarize_node(state)

        assert result["agent_to_route_to"] == "methodology"
        assert result["current_phase"] == "methodology"
        assert result["forwarded_message"] == "proceed to study design"


# ---------------------------------------------------------------------------
# Methodology
# ---------------------------------------------------------------------------

class TestMethodologyNode:
    async def test_routes_to_biostatistics(self, patch_get_chat_model):
        output = MethodologyOutput(
            direct_response_to_user="Study design complete.",
            agent_to_route_to="biostatistics",
            forwarded_message="RCT design for diabetes",
        )
        patch_get_chat_model("app.agents.methodology", output)
        state = base_state(current_phase="methodology")

        result = await methodology_node(state)

        assert result["agent_to_route_to"] == "biostatistics"
        assert result["current_phase"] == "biostatistics"


# ---------------------------------------------------------------------------
# Biostatistics
# ---------------------------------------------------------------------------

class TestBiostatisticsNode:
    async def test_need_info(self, patch_get_chat_model):
        output = BiostatisticsOutput(
            direct_response_to_user="What is the effect size?",
            need_info=True,
        )
        patch_get_chat_model("app.agents.biostatistics", output)
        state = base_state(current_phase="biostatistics")

        result = await biostatistics_node(state)

        assert result["need_info"] is True
        assert "effect size" in result["messages"][0].content

    async def test_diagnostic_query(self, patch_get_chat_model):
        output = BiostatisticsOutput(
            direct_response_to_user="Running diagnostic.",
            diagnostic_query="two groups, continuous, normal distribution",
        )
        mock = patch_get_chat_model("app.agents.biostatistics", output)

        # Also mock the diagnostic LLM call (non-structured)
        diagnostic_mock = MagicMock()
        diagnostic_mock.ainvoke = AsyncMock(return_value=MagicMock(content="Use t-test"))

        models = {"biostatistics": mock, "diagnostic": diagnostic_mock}

        def side_effect(agent_name):
            return models[agent_name]

        with patch("app.agents.biostatistics.get_chat_model", side_effect=side_effect):
            state = base_state(current_phase="biostatistics")
            result = await biostatistics_node(state)

        assert "Diagnostic Tool Recommendation" in result["messages"][0].content


# ---------------------------------------------------------------------------
# Coding -- Generate & Execute (Path A)
# ---------------------------------------------------------------------------

class TestCodingNode:
    async def test_generate_and_execute(self, patch_get_chat_model):
        """Path A: LLM generates python_script, code is executed, results shown."""
        output = CodingOutput(
            direct_response_to_user="Calculating sample size.",
            python_script="from statsmodels.stats.power import TTestIndPower\nanalysis = TTestIndPower()\nn = analysis.solve_power(effect_size=0.5, alpha=0.05, power=0.8)\nprint(f'Sample size per group: {n:.0f}')",
        )
        patch_get_chat_model("app.agents.biostatistics", output)

        exec_result = ExecutionResult(
            success=True,
            stdout="Sample size per group: 64",
            error_message="",
        )

        with patch("app.agents.biostatistics.execute_python", return_value=exec_result):
            state = base_state(
                current_phase="biostatistics",
                forwarded_message="generate power analysis code",
            )
            result = await coding_node(state)

        assert result["has_pending_code"] is True
        assert "statsmodels" in result["stored_python_script"]
        assert result["execution_result"]["success"] is True
        assert "64" in result["messages"][0].content
        assert result["code_output"] == {}  # No code emitted until user asks

    async def test_execution_failure_graceful(self, patch_get_chat_model):
        """Path A: When execution fails, error is reported gracefully."""
        output = CodingOutput(
            direct_response_to_user="Calculating...",
            python_script="import broken_module",
        )
        patch_get_chat_model("app.agents.biostatistics", output)

        exec_result = ExecutionResult(
            success=False,
            stdout="",
            error_message="ModuleNotFoundError: No module named 'broken_module'",
        )

        with patch("app.agents.biostatistics.execute_python", return_value=exec_result):
            state = base_state(
                current_phase="biostatistics",
                forwarded_message="calculate",
            )
            result = await coding_node(state)

        assert result["has_pending_code"] is True
        assert result["execution_result"]["success"] is False
        assert "issue" in result["messages"][0].content.lower()

    async def test_no_script_generated(self, patch_get_chat_model):
        """Path A: When LLM generates no script, no execution happens."""
        output = CodingOutput(
            direct_response_to_user="No code needed for this explanation.",
        )
        patch_get_chat_model("app.agents.biostatistics", output)

        state = base_state(
            current_phase="biostatistics",
            forwarded_message="explain concept",
        )
        result = await coding_node(state)

        assert result["has_pending_code"] is False
        assert result["stored_python_script"] == ""
        assert result["execution_result"] == {}
        assert result["code_output"] == {}

    async def test_cross_phase_routing(self, patch_get_chat_model):
        """Path A: coding node can route to another phase."""
        output = CodingOutput(
            direct_response_to_user="Done, moving to methodology.",
            agent_to_route_to="methodology",
            forwarded_message="review design",
        )
        patch_get_chat_model("app.agents.biostatistics", output)

        with patch("app.agents.biostatistics.execute_python", return_value=ExecutionResult(True, "", "")):
            state = base_state(
                current_phase="biostatistics",
                forwarded_message="code done",
            )
            result = await coding_node(state)

        assert result["agent_to_route_to"] == "methodology"
        assert result["current_phase"] == "methodology"


# ---------------------------------------------------------------------------
# Coding -- Serve Code (Path B)
# ---------------------------------------------------------------------------

class TestCodingNodeServeCode:
    async def test_serve_python_code(self):
        """Path B: user requests Python code, stored script is returned."""
        state = base_state(
            current_phase="biostatistics",
            has_pending_code=True,
            stored_python_script="print('hello')",
            messages=[HumanMessage(content="Show me the Python code")],
        )
        result = await coding_node(state)

        assert result["code_output"]["language"] == "python"
        assert result["code_output"]["script"] == "print('hello')"
        assert result["has_pending_code"] is False

    async def test_serve_r_code(self, patch_get_chat_model):
        """Path B: user requests R code, script is translated."""
        # Mock the LLM for translation (non-structured call)
        r_code = "cat('hello')"
        mock_llm = MagicMock()
        mock_llm.ainvoke = AsyncMock(return_value=MagicMock(content=r_code))

        state = base_state(
            current_phase="biostatistics",
            has_pending_code=True,
            stored_python_script="print('hello')",
            messages=[HumanMessage(content="Can I get that in R code?")],
        )

        with patch("app.agents.biostatistics.get_chat_model", return_value=mock_llm):
            result = await coding_node(state)

        assert result["code_output"]["language"] == "r"
        assert result["code_output"]["script"] == r_code
        assert result["has_pending_code"] is False

    async def test_serve_stata_code(self, patch_get_chat_model):
        """Path B: user requests STATA code, script is translated."""
        stata_code = 'display "hello"'
        mock_llm = MagicMock()
        mock_llm.ainvoke = AsyncMock(return_value=MagicMock(content=stata_code))

        state = base_state(
            current_phase="biostatistics",
            has_pending_code=True,
            stored_python_script="print('hello')",
            messages=[HumanMessage(content="Give me the STATA script")],
        )

        with patch("app.agents.biostatistics.get_chat_model", return_value=mock_llm):
            result = await coding_node(state)

        assert result["code_output"]["language"] == "stata"
        assert result["code_output"]["script"] == stata_code
        assert result["has_pending_code"] is False

    async def test_non_code_message_with_pending_code_runs_path_a(self, patch_get_chat_model):
        """When has_pending_code=True but user message is not a code request, use Path A."""
        output = CodingOutput(
            direct_response_to_user="Recalculating with new params.",
            python_script="print(200)",
        )
        patch_get_chat_model("app.agents.biostatistics", output)

        exec_result = ExecutionResult(success=True, stdout="200", error_message="")

        with patch("app.agents.biostatistics.execute_python", return_value=exec_result):
            state = base_state(
                current_phase="biostatistics",
                has_pending_code=True,
                stored_python_script="print('old')",
                forwarded_message="recalculate with alpha=0.01",
                messages=[HumanMessage(content="Use alpha 0.01 instead")],
            )
            result = await coding_node(state)

        assert result["has_pending_code"] is True
        assert "200" in result["messages"][0].content
