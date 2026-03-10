"""Tests for judge prompt building, including multi-turn support."""

from evaluation.rubrics.schema import RubricDimension, ScoreAnchor
from evaluation.llm_judge.judge_prompt import (
    MULTI_TURN_JUDGE_ADDENDUM,
    build_evaluation_prompt,
    build_overall_quality_prompt,
    _format_conversation_turns,
)


def _make_dimension() -> RubricDimension:
    return RubricDimension(
        dimension_id="T1",
        name="Test Dimension",
        description="For testing",
        anchors=[
            ScoreAnchor(score=i, label=f"Level {i}", description=f"Desc {i}")
            for i in range(1, 6)
        ],
    )


class TestFormatConversationTurns:
    def test_single_turn(self):
        result = _format_conversation_turns(
            ["Hello?"], ["Hi there."]
        )
        assert "Turn 1" in result
        assert "Hello?" in result
        assert "Hi there." in result

    def test_multi_turn(self):
        result = _format_conversation_turns(
            ["Q1", "Q2", "Q3"],
            ["A1", "A2", "A3"],
        )
        assert "Turn 1" in result
        assert "Turn 2" in result
        assert "Turn 3" in result
        assert "Q2" in result
        assert "A3" in result


class TestBuildEvaluationPrompt:
    def test_single_turn_no_addendum(self):
        prompt = build_evaluation_prompt(
            dimension=_make_dimension(),
            case_context="Test context",
            user_prompt="What test?",
            response_text="Use a t-test.",
            expertise_mode="simple",
        )
        assert "MULTI-TURN" not in prompt
        assert "User Prompt" in prompt
        assert "What test?" in prompt
        assert "Use a t-test." in prompt

    def test_multi_turn_includes_addendum(self):
        prompt = build_evaluation_prompt(
            dimension=_make_dimension(),
            case_context="Test context",
            user_prompt="Initial question",
            response_text="Initial answer",
            expertise_mode="simple",
            follow_up_prompts=["Follow-up question"],
            follow_up_responses=["Follow-up answer"],
        )
        assert "MULTI-TURN" in prompt
        assert "Context Retention" in prompt
        assert "Conversation Thread" in prompt
        assert "Turn 1" in prompt
        assert "Turn 2" in prompt
        assert "Initial question" in prompt
        assert "Follow-up answer" in prompt

    def test_multi_turn_omits_single_prompt_section(self):
        prompt = build_evaluation_prompt(
            dimension=_make_dimension(),
            case_context="Context",
            user_prompt="Q1",
            response_text="A1",
            expertise_mode="advanced",
            follow_up_prompts=["Q2"],
            follow_up_responses=["A2"],
        )
        # Multi-turn should NOT have "## User Prompt:" section
        # It should have "## Conversation Thread:" instead
        assert "## Conversation Thread:" in prompt

    def test_code_output_appended(self):
        prompt = build_evaluation_prompt(
            dimension=_make_dimension(),
            case_context="Ctx",
            user_prompt="Q",
            response_text="A",
            expertise_mode="simple",
            code_output="print(42)",
            follow_up_prompts=["Q2"],
            follow_up_responses=["A2"],
        )
        assert "Code Output" in prompt
        assert "print(42)" in prompt


class TestBuildOverallQualityPrompt:
    def test_single_turn(self):
        prompt = build_overall_quality_prompt(
            case_context="Context",
            user_prompt="Question",
            response_text="Answer",
            expertise_mode="simple",
            agent_type="methodology",
        )
        assert "MULTI-TURN" not in prompt
        assert "Response to Evaluate" in prompt

    def test_multi_turn(self):
        prompt = build_overall_quality_prompt(
            case_context="Context",
            user_prompt="Q1",
            response_text="A1",
            expertise_mode="advanced",
            agent_type="biostatistics",
            follow_up_prompts=["Q2", "Q3"],
            follow_up_responses=["A2", "A3"],
        )
        assert "MULTI-TURN" in prompt
        assert "Conversation Thread" in prompt
        assert "Turn 1" in prompt
        assert "Turn 3" in prompt


class TestMultiTurnAddendum:
    def test_addendum_has_key_criteria(self):
        assert "Context Retention" in MULTI_TURN_JUDGE_ADDENDUM
        assert "Conversation Coherence" in MULTI_TURN_JUDGE_ADDENDUM
        assert "Completeness Across Turns" in MULTI_TURN_JUDGE_ADDENDUM
        assert "Clarification Quality" in MULTI_TURN_JUDGE_ADDENDUM
        assert "Progressive Depth" in MULTI_TURN_JUDGE_ADDENDUM
