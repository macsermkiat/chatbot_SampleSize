"""Blind responses by stripping system-identifying markers and assigning random labels."""

from __future__ import annotations

import random
import re
from dataclasses import dataclass

from evaluation.collectors.chatbot_collector import CollectedResponse


@dataclass(frozen=True)
class BlindedResponse:
    """A response with system identity hidden."""

    case_id: str
    blinded_label: str  # "system_a" or "system_b"
    true_identity: str  # "chatbot" or "gpt5" (hidden from judge)
    text: str
    code: str
    has_execution_result: bool


@dataclass(frozen=True)
class BlindedPair:
    """A pair of blinded responses for the same case."""

    case_id: str
    system_a: BlindedResponse
    system_b: BlindedResponse
    # Mapping revealed only after evaluation
    label_to_identity: dict[str, str]


# Patterns to strip from chatbot responses to prevent identification
CHATBOT_IDENTIFIERS = [
    (r"### Diagnostic Tool Recommendation\b", "### Statistical Test Recommendation"),
    (r"(?i)\bcoding agent\b", "the system"),
    (r"(?i)\bbiostatistics agent\b", "the system"),
    (r"(?i)\bmethodology agent\b", "the system"),
    (r"(?i)\borchestrator\b", "the system"),
    (r"(?i)\bsecretary agent\b", "the system"),
    (r"(?i)\bresearch gap (?:search |summarize )?agent\b", "the system"),
    (r"(?i)\bphase transition\b", "next step"),
    (r"(?i)\brouting to \w+\b", "proceeding"),
    (r"(?i)\bforwarded message\b", "context"),
]

# Patterns to strip from GPT-5 responses
GPT5_IDENTIFIERS = [
    (r"(?i)\bas an AI language model\b", ""),
    (r"(?i)\bI'm ChatGPT\b", ""),
    (r"(?i)\bOpenAI\b", ""),
    (r"(?i)\bGPT-[45]\b", ""),
]


def blind_response(response: CollectedResponse, label: str) -> BlindedResponse:
    """Strip identifying markers from a response."""
    text = response.response_text

    # Apply system-specific stripping
    if response.system_id == "chatbot":
        for pattern, replacement in CHATBOT_IDENTIFIERS:
            text = re.sub(pattern, replacement, text)
    elif response.system_id == "gpt5":
        for pattern, replacement in GPT5_IDENTIFIERS:
            text = re.sub(pattern, replacement, text)

    # Normalize markdown formatting
    text = _normalize_markdown(text)

    code = response.code_output
    # Strip system-specific code comments
    if code:
        code = re.sub(r"#.*agent.*\n", "\n", code, flags=re.IGNORECASE)

    return BlindedResponse(
        case_id=response.case_id,
        blinded_label=label,
        true_identity=response.system_id,
        text=text.strip(),
        code=code.strip() if code else "",
        has_execution_result=bool(response.execution_result),
    )


def create_blinded_pairs(
    chatbot_responses: dict[str, list[CollectedResponse]],
    gpt5_responses: dict[str, list[CollectedResponse]],
    seed: int = 42,
) -> list[BlindedPair]:
    """Create blinded response pairs for all cases.

    Randomly assigns which system gets label 'system_a' vs 'system_b'
    for each case independently.
    """
    rng = random.Random(seed)
    pairs: list[BlindedPair] = []

    all_case_ids = set(chatbot_responses.keys()) & set(gpt5_responses.keys())

    for case_id in sorted(all_case_ids):
        chatbot_text = _merge_turns(chatbot_responses[case_id])
        gpt5_text = _merge_turns(gpt5_responses[case_id])

        # Randomly assign labels
        if rng.random() < 0.5:
            a_label, b_label = "chatbot", "gpt5"
            a_resp, b_resp = chatbot_text, gpt5_text
        else:
            a_label, b_label = "gpt5", "chatbot"
            a_resp, b_resp = gpt5_text, chatbot_text

        system_a = blind_response(a_resp, "system_a")
        system_b = blind_response(b_resp, "system_b")

        pairs.append(
            BlindedPair(
                case_id=case_id,
                system_a=system_a,
                system_b=system_b,
                label_to_identity={
                    "system_a": a_label,
                    "system_b": b_label,
                },
            )
        )

    return pairs


def _merge_turns(responses: list[CollectedResponse]) -> CollectedResponse:
    """Merge multi-turn responses into a single response for evaluation."""
    if len(responses) == 1:
        return responses[0]

    merged_text = "\n\n---\n\n".join(
        f"**Turn {r.turn_number}:**\n{r.response_text}" for r in responses
    )
    merged_code = "\n\n".join(r.code_output for r in responses if r.code_output)

    return CollectedResponse(
        case_id=responses[0].case_id,
        system_id=responses[0].system_id,
        session_id=responses[0].session_id,
        turn_number=0,
        prompt=responses[0].prompt,
        response_text=merged_text,
        code_output=merged_code,
        execution_result=responses[-1].execution_result,
        phase_transitions=responses[0].phase_transitions,
        latency_ms=sum(r.latency_ms for r in responses),
        expertise_mode=responses[0].expertise_mode,
    )


def _normalize_markdown(text: str) -> str:
    """Normalize markdown formatting to prevent identification by style."""
    # Standardize heading levels
    text = re.sub(r"^#{4,}", "###", text, flags=re.MULTILINE)
    # Remove excessive blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text
