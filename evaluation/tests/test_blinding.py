"""Tests for response blinding and pair creation."""

from evaluation.collectors.chatbot_collector import CollectedResponse
from evaluation.llm_judge.blinding import (
    blind_response,
    create_blinded_pairs,
    _normalize_markdown,
)


def _make_response(
    case_id: str = "T01",
    system_id: str = "chatbot",
    text: str = "Test response",
    code: str = "",
) -> CollectedResponse:
    return CollectedResponse(
        case_id=case_id,
        system_id=system_id,
        session_id="test-session",
        turn_number=1,
        prompt="test prompt",
        response_text=text,
        code_output=code,
        execution_result="",
        phase_transitions=(),
        latency_ms=100.0,
        expertise_mode="simple",
    )


class TestBlindResponse:
    def test_strips_chatbot_agent_names(self):
        response = _make_response(
            text="The coding agent will handle this. The biostatistics agent recommends..."
        )
        blinded = blind_response(response, "system_a")
        assert "coding agent" not in blinded.text
        assert "biostatistics agent" not in blinded.text
        assert "the system" in blinded.text

    def test_strips_gpt5_identifiers(self):
        response = _make_response(
            system_id="gpt5",
            text="As an AI language model created by OpenAI, I'm ChatGPT and I can help."
        )
        blinded = blind_response(response, "system_b")
        assert "OpenAI" not in blinded.text
        assert "ChatGPT" not in blinded.text

    def test_preserves_content(self):
        response = _make_response(text="Use a t-test for comparison.")
        blinded = blind_response(response, "system_a")
        assert "t-test" in blinded.text

    def test_strips_code_agent_comments(self):
        response = _make_response(code="# biostatistics agent output\nprint(42)")
        blinded = blind_response(response, "system_a")
        assert "agent" not in blinded.code.lower()
        assert "print(42)" in blinded.code

    def test_preserves_true_identity(self):
        response = _make_response(system_id="chatbot")
        blinded = blind_response(response, "system_a")
        assert blinded.true_identity == "chatbot"
        assert blinded.blinded_label == "system_a"


class TestCreateBlindedPairs:
    def test_creates_pairs_for_matching_cases(self):
        chatbot = {
            "T01": [_make_response("T01", "chatbot", "Chatbot response 1")],
            "T02": [_make_response("T02", "chatbot", "Chatbot response 2")],
        }
        gpt5 = {
            "T01": [_make_response("T01", "gpt5", "GPT5 response 1")],
            "T02": [_make_response("T02", "gpt5", "GPT5 response 2")],
        }
        pairs = create_blinded_pairs(chatbot, gpt5)
        assert len(pairs) == 2

    def test_only_pairs_common_cases(self):
        chatbot = {
            "T01": [_make_response("T01", "chatbot")],
            "T03": [_make_response("T03", "chatbot")],
        }
        gpt5 = {
            "T01": [_make_response("T01", "gpt5")],
            "T02": [_make_response("T02", "gpt5")],
        }
        pairs = create_blinded_pairs(chatbot, gpt5)
        assert len(pairs) == 1
        assert pairs[0].case_id == "T01"

    def test_random_label_assignment(self):
        chatbot = {f"T{i:02d}": [_make_response(f"T{i:02d}", "chatbot")] for i in range(20)}
        gpt5 = {f"T{i:02d}": [_make_response(f"T{i:02d}", "gpt5")] for i in range(20)}
        pairs = create_blinded_pairs(chatbot, gpt5, seed=42)

        # With randomization, not all system_a should be the same identity
        a_identities = [p.label_to_identity["system_a"] for p in pairs]
        assert "chatbot" in a_identities
        assert "gpt5" in a_identities

    def test_deterministic_with_seed(self):
        chatbot = {"T01": [_make_response("T01", "chatbot")]}
        gpt5 = {"T01": [_make_response("T01", "gpt5")]}

        pairs1 = create_blinded_pairs(chatbot, gpt5, seed=42)
        pairs2 = create_blinded_pairs(chatbot, gpt5, seed=42)

        assert pairs1[0].label_to_identity == pairs2[0].label_to_identity


class TestNormalizeMarkdown:
    def test_caps_heading_levels(self):
        text = "##### Deep heading\n###### Deeper"
        result = _normalize_markdown(text)
        assert "### Deep heading" in result
        assert "### Deeper" in result

    def test_removes_excessive_blank_lines(self):
        text = "line1\n\n\n\n\nline2"
        result = _normalize_markdown(text)
        assert "\n\n\n" not in result
        assert "line1\n\nline2" == result
