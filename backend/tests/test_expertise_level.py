"""Tests for the expertise level (simple/advanced) feature.

Covers: prompt_composer, ChatRequest validation, agent node prompt selection,
and backward compatibility.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.agents.prompt_composer import get_prompt
from app.agents.prompts import (
    ADVANCED_STYLE_DIRECTIVE,
    BIOSTATS_PROMPT,
    CODING_PROMPT,
    DIAGNOSTIC_PROMPT,
    GAP_SEARCH_PROMPT,
    GAP_SUMMARIZE_PROMPT,
    METHODOLOGY_PROMPT,
    ORCHESTRATOR_PROMPT,
    SIMPLE_ADDENDA,
    SIMPLE_BIOSTATS_ADDENDUM,
    SIMPLE_CODING_ADDENDUM,
    SIMPLE_DIAGNOSTIC_ADDENDUM,
    SIMPLE_GAP_SUMMARIZE_ADDENDUM,
    SIMPLE_METHODOLOGY_ADDENDUM,
    SIMPLE_ORCHESTRATOR_ADDENDUM,
    SIMPLE_STYLE_DIRECTIVE,
    WELCOME_MESSAGE,
    WELCOME_MESSAGE_SIMPLE,
)
from app.agents.state import (
    BiostatisticsOutput,
    CodingOutput,
    GapSearchOutput,
    GapSummarizeOutput,
    MethodologyOutput,
    OrchestratorOutput,
)
from app.models import ChatRequest

from tests.conftest import base_state, make_mock_llm


# ===========================================================================
# 1. prompt_composer.get_prompt tests
# ===========================================================================

class TestGetPrompt:
    """Test the prompt composition logic."""

    def test_simple_mode_prepends_simple_directive(self):
        result = get_prompt(ORCHESTRATOR_PROMPT, "simple", "orchestrator")
        assert result.startswith(SIMPLE_STYLE_DIRECTIVE)

    def test_advanced_mode_prepends_advanced_directive(self):
        result = get_prompt(ORCHESTRATOR_PROMPT, "advanced", "orchestrator")
        assert result.startswith(ADVANCED_STYLE_DIRECTIVE)

    def test_simple_mode_includes_base_prompt(self):
        result = get_prompt(ORCHESTRATOR_PROMPT, "simple", "orchestrator")
        assert ORCHESTRATOR_PROMPT in result

    def test_advanced_mode_includes_base_prompt(self):
        result = get_prompt(ORCHESTRATOR_PROMPT, "advanced", "orchestrator")
        assert ORCHESTRATOR_PROMPT in result

    def test_simple_mode_appends_agent_addendum(self):
        result = get_prompt(ORCHESTRATOR_PROMPT, "simple", "orchestrator")
        assert SIMPLE_ORCHESTRATOR_ADDENDUM in result

    def test_simple_mode_gap_summarize_addendum(self):
        result = get_prompt(GAP_SUMMARIZE_PROMPT, "simple", "gap_summarize")
        assert SIMPLE_GAP_SUMMARIZE_ADDENDUM in result

    def test_simple_mode_methodology_addendum(self):
        result = get_prompt(METHODOLOGY_PROMPT, "simple", "methodology")
        assert SIMPLE_METHODOLOGY_ADDENDUM in result

    def test_simple_mode_biostats_addendum(self):
        result = get_prompt(BIOSTATS_PROMPT, "simple", "biostatistics")
        assert SIMPLE_BIOSTATS_ADDENDUM in result

    def test_simple_mode_coding_addendum(self):
        result = get_prompt(CODING_PROMPT, "simple", "coding")
        assert SIMPLE_CODING_ADDENDUM in result

    def test_simple_mode_diagnostic_addendum(self):
        result = get_prompt(DIAGNOSTIC_PROMPT, "simple", "diagnostic")
        assert SIMPLE_DIAGNOSTIC_ADDENDUM in result

    def test_simple_mode_gap_search_no_addendum(self):
        """gap_search has no user-facing simple addendum (internal search terms)."""
        result = get_prompt(GAP_SEARCH_PROMPT, "simple", "gap_search")
        # Contains style directive but no extra addendum beyond what's in SIMPLE_ADDENDA
        assert SIMPLE_STYLE_DIRECTIVE in result
        assert GAP_SEARCH_PROMPT in result

    def test_advanced_mode_no_addenda(self):
        """Advanced mode should not include any simple-mode addenda."""
        result = get_prompt(ORCHESTRATOR_PROMPT, "advanced", "orchestrator")
        assert SIMPLE_ORCHESTRATOR_ADDENDUM not in result

    def test_unknown_expertise_defaults_to_advanced(self):
        """Unknown expertise_level values should fall back to advanced."""
        result = get_prompt(ORCHESTRATOR_PROMPT, "unknown", "orchestrator")
        assert result.startswith(ADVANCED_STYLE_DIRECTIVE)

    def test_unknown_agent_no_addendum(self):
        """Unknown agent_name should still compose a valid prompt with no addendum."""
        result = get_prompt(ORCHESTRATOR_PROMPT, "simple", "nonexistent_agent")
        assert SIMPLE_STYLE_DIRECTIVE in result
        assert ORCHESTRATOR_PROMPT in result

    def test_routing_instructions_preserved_in_simple_mode(self):
        """Simple mode must not remove routing instructions."""
        for prompt, name in [
            (ORCHESTRATOR_PROMPT, "orchestrator"),
            (GAP_SUMMARIZE_PROMPT, "gap_summarize"),
            (METHODOLOGY_PROMPT, "methodology"),
            (CODING_PROMPT, "coding"),
        ]:
            result = get_prompt(prompt, "simple", name)
            assert "agent_to_route_to" in result, f"Routing missing in simple {name}"


# ===========================================================================
# 2. ChatRequest model validation
# ===========================================================================

class TestChatRequestExpertiseLevel:
    """Test expertise_level field on ChatRequest."""

    def test_default_is_none(self):
        """Default expertise_level is None (omit to keep existing session value)."""
        req = ChatRequest(message="test")
        assert req.expertise_level is None

    def test_accepts_simple(self):
        req = ChatRequest(message="test", expertise_level="simple")
        assert req.expertise_level == "simple"

    def test_accepts_advanced(self):
        req = ChatRequest(message="test", expertise_level="advanced")
        assert req.expertise_level == "advanced"

    def test_rejects_invalid_value(self):
        with pytest.raises(ValidationError):
            ChatRequest(message="test", expertise_level="expert")

    def test_rejects_empty_string(self):
        with pytest.raises(ValidationError):
            ChatRequest(message="test", expertise_level="")


# ===========================================================================
# 3. Agent nodes use expertise_level from state
# ===========================================================================

class TestAgentNodeExpertiseLevel:
    """Verify each agent node reads expertise_level from state and passes it to get_prompt."""

    @pytest.mark.asyncio
    async def test_orchestrator_uses_expertise_level(self, patch_get_chat_model):
        from unittest.mock import patch as _patch

        output = OrchestratorOutput(
            direct_response_to_user="Hello",
            agent_to_route_to="research_gap",
            forwarded_message="context",
        )
        patch_get_chat_model("app.agents.orchestrator", output)

        state = base_state(expertise_level="simple")

        with _patch("app.agents.orchestrator.get_prompt", wraps=get_prompt) as mock_gp:
            from app.agents.orchestrator import orchestrator_node
            await orchestrator_node(state)
            mock_gp.assert_called_once()
            call_args = mock_gp.call_args
            assert call_args[0][1] == "simple"  # expertise_level
            assert call_args[0][2] == "orchestrator"  # agent_name

    @pytest.mark.asyncio
    async def test_methodology_uses_expertise_level(self, patch_get_chat_model):
        from unittest.mock import patch as _patch

        output = MethodologyOutput(
            direct_response_to_user="Study design advice",
        )
        patch_get_chat_model("app.agents.methodology", output)

        state = base_state(
            expertise_level="simple",
            current_phase="methodology",
        )

        with _patch("app.agents.methodology.get_prompt", wraps=get_prompt) as mock_gp:
            from app.agents.methodology import methodology_node
            await methodology_node(state)
            mock_gp.assert_called_once()
            assert mock_gp.call_args[0][1] == "simple"
            assert mock_gp.call_args[0][2] == "methodology"

    @pytest.mark.asyncio
    async def test_gap_summarize_uses_expertise_level(self, patch_get_chat_model):
        from unittest.mock import patch as _patch

        output = GapSummarizeOutput(
            direct_response_to_user="Gap analysis",
        )
        patch_get_chat_model("app.agents.research_gap", output)

        state = base_state(
            expertise_level="simple",
            current_phase="research_gap",
            search_results=[{"url": "https://test.com", "title": "T", "content": "C", "score": 0.9}],
            search_count=1,
        )

        with _patch("app.agents.research_gap.get_prompt", wraps=get_prompt) as mock_gp:
            from app.agents.research_gap import gap_summarize_node
            await gap_summarize_node(state)
            # gap_summarize_node calls get_prompt once
            assert mock_gp.call_count == 1
            assert mock_gp.call_args[0][1] == "simple"
            assert mock_gp.call_args[0][2] == "gap_summarize"

    @pytest.mark.asyncio
    async def test_biostatistics_uses_expertise_level(self, patch_get_chat_model):
        from unittest.mock import patch as _patch

        output = BiostatisticsOutput(
            direct_response_to_user="Stats advice",
            need_info=True,
        )
        patch_get_chat_model("app.agents.biostatistics", output)

        state = base_state(
            expertise_level="simple",
            current_phase="biostatistics",
        )

        with _patch("app.agents.biostatistics.get_prompt", wraps=get_prompt) as mock_gp:
            from app.agents.biostatistics import biostatistics_node
            await biostatistics_node(state)
            assert mock_gp.call_count == 1
            assert mock_gp.call_args[0][1] == "simple"
            assert mock_gp.call_args[0][2] == "biostatistics"

    @pytest.mark.asyncio
    async def test_coding_uses_expertise_level(self, patch_get_chat_model):
        from unittest.mock import patch as _patch

        output = CodingOutput(
            direct_response_to_user="Code output",
        )
        patch_get_chat_model("app.agents.biostatistics", output)

        state = base_state(
            expertise_level="simple",
            current_phase="biostatistics",
            forwarded_message="Calculate sample size",
        )

        with _patch("app.agents.biostatistics.get_prompt", wraps=get_prompt) as mock_gp:
            from app.agents.biostatistics import coding_node
            await coding_node(state)
            assert mock_gp.call_count == 1
            assert mock_gp.call_args[0][1] == "simple"
            assert mock_gp.call_args[0][2] == "coding"


# ===========================================================================
# 4. Backward compatibility
# ===========================================================================

class TestBackwardCompatibility:
    """Ensure existing sessions without expertise_level still work."""

    def test_base_state_defaults_to_advanced(self):
        state = base_state()
        assert state["expertise_level"] == "advanced"

    @pytest.mark.asyncio
    async def test_orchestrator_defaults_when_missing(self, patch_get_chat_model):
        """When expertise_level is missing from state, should default to 'advanced'."""
        from unittest.mock import patch as _patch

        output = OrchestratorOutput(
            direct_response_to_user="Hello",
        )
        patch_get_chat_model("app.agents.orchestrator", output)

        # Simulate an old state without expertise_level
        state = base_state()
        del state["expertise_level"]

        with _patch("app.agents.orchestrator.get_prompt", wraps=get_prompt) as mock_gp:
            from app.agents.orchestrator import orchestrator_node
            await orchestrator_node(state)
            assert mock_gp.call_args[0][1] == "advanced"


# ===========================================================================
# 5. Welcome message variants
# ===========================================================================

class TestWelcomeMessages:
    """Verify separate welcome messages exist for each expertise level."""

    def test_advanced_welcome_mentions_pico(self):
        assert "PICO" in WELCOME_MESSAGE

    def test_simple_welcome_no_pico(self):
        assert "PICO" not in WELCOME_MESSAGE_SIMPLE

    def test_simple_welcome_plain_language(self):
        assert "plain language" in WELCOME_MESSAGE_SIMPLE.lower()

    def test_both_welcome_have_disclaimer(self):
        assert "not" in WELCOME_MESSAGE.lower() and "medical advice" in WELCOME_MESSAGE.lower()
        assert "not" in WELCOME_MESSAGE_SIMPLE.lower() and "medical advice" in WELCOME_MESSAGE_SIMPLE.lower()


# ===========================================================================
# 6. Prompt content quality checks
# ===========================================================================

class TestPromptContentQuality:
    """Verify simple-mode addenda include key plain-language concepts."""

    def test_simple_biostats_explains_power(self):
        """The composed simple biostats prompt must explain power in plain language."""
        composed = get_prompt(BIOSTATS_PROMPT, "simple", "biostatistics").lower()
        assert "how many patients" in composed

    def test_simple_biostats_explains_effect_size(self):
        """The composed simple biostats prompt must explain effect size in plain language."""
        composed = get_prompt(BIOSTATS_PROMPT, "simple", "biostatistics").lower()
        assert "how big" in composed

    def test_simple_methodology_avoids_dag(self):
        assert "Do NOT use DAG notation" in SIMPLE_METHODOLOGY_ADDENDUM

    def test_simple_methodology_uses_analogies(self):
        assert "analogy" in SIMPLE_METHODOLOGY_ADDENDUM.lower() or "analogies" in SIMPLE_METHODOLOGY_ADDENDUM.lower()

    def test_simple_gap_summarize_skips_grade(self):
        assert "Skip GRADE" in SIMPLE_GAP_SUMMARIZE_ADDENDUM

    def test_simple_orchestrator_warm_tone(self):
        assert "warm" in SIMPLE_ORCHESTRATOR_ADDENDUM.lower() or "reassuring" in SIMPLE_ORCHESTRATOR_ADDENDUM.lower()

    def test_simple_coding_generates_script_but_plain_results(self):
        """Simple coding addendum must still generate python_script for execution."""
        lower = SIMPLE_CODING_ADDENDUM.lower()
        assert "python_script" in lower
        assert "plain english" in lower

    def test_simple_diagnostic_recommendation_format(self):
        assert "you should use" in SIMPLE_DIAGNOSTIC_ADDENDUM.lower()
