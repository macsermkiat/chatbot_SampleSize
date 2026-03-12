"""LLM judge prompt templates for evaluation scoring."""

from __future__ import annotations

from typing import Sequence

from evaluation.rubrics.schema import Rubric, RubricDimension

# ---------------------------------------------------------------------------
# Shared evaluation rules (used by both single-dimension and batch prompts)
# ---------------------------------------------------------------------------
_EVALUATION_RULES = """\
EVALUATION RULES:
1. Score each dimension independently. Do not let one dimension's quality \
   influence another's score.
2. Use the anchor descriptions as your primary guide. Match the response \
   to the closest anchor.
3. Be consistent: a response that meets anchor 3's description should \
   receive a 3, not a 2 or 4.
4. Consider the expertise mode: "simple" mode responses should use \
   plain language; "advanced" mode should use precise terminology.
5. Provide specific evidence from the response to justify each score.
6. Do NOT consider formatting, length, or style -- focus on content \
   quality and accuracy.
7. Both response styles are equally valid: (a) a system that asks \
   clarifying questions and then provides a tailored answer, and (b) a \
   system that provides a comprehensive answer with clearly stated \
   assumptions. Neither approach is inherently better. Score the QUALITY \
   and ACCURACY of the final substantive content, regardless of how many \
   turns it took.
8. For multi-turn conversations, evaluate the FINAL state of the \
   complete conversation, not just the first turn. A multi-turn exchange \
   that reaches the same quality as a single comprehensive response \
   should receive the same score."""

# ---------------------------------------------------------------------------
# Single-dimension system prompt (legacy, kept for backwards compatibility)
# ---------------------------------------------------------------------------
JUDGE_SYSTEM_PROMPT = f"""\
You are an expert evaluator of medical research AI assistants. You have \
deep expertise in clinical epidemiology, biostatistics, and research \
methodology.

Your task is to evaluate a response from an AI system that helps medical \
researchers with study design, methodology, and statistical analysis. \
You will score the response on a specific dimension using a 1-5 scale \
with detailed anchors.

{_EVALUATION_RULES}

OUTPUT FORMAT:
You must respond with ONLY a valid JSON object (no markdown fences):
{{
  "score": <integer 1-5>,
  "reasoning": "<2-3 sentences explaining why this score>",
  "evidence": "<specific quote or element from the response>"
}}
"""

# ---------------------------------------------------------------------------
# Batch system prompt -- scores ALL dimensions + overall in one call
# ---------------------------------------------------------------------------
JUDGE_BATCH_SYSTEM_PROMPT = f"""\
You are an expert evaluator of medical research AI assistants. You have \
deep expertise in clinical epidemiology, biostatistics, and research \
methodology.

Your task is to evaluate a response from an AI system across ALL \
dimensions listed below, PLUS an overall quality assessment. Score each \
dimension on a 1-5 scale using the anchors provided.

{_EVALUATION_RULES}

OUTPUT FORMAT:
You must respond with ONLY a valid JSON object (no markdown fences). \
The object must have a "dimensions" array and an "overall" object:
{{
  "dimensions": [
    {{
      "dimension_id": "<e.g. M1 or B3>",
      "score": <integer 1-5>,
      "reasoning": "<2-3 sentences>",
      "evidence": "<specific quote>"
    }}
  ],
  "overall": {{
    "score": <integer 1-5>,
    "reasoning": "<2-3 sentences>"
  }}
}}
"""


MULTI_TURN_JUDGE_ADDENDUM = """\

MULTI-TURN CONVERSATION CONTEXT:
This is a multi-turn conversation. You are evaluating the FULL conversation \
thread, not just one response. When scoring, consider:

1. **Context Retention**: Does the system correctly use information from \
   earlier turns? Does it maintain awareness of what was previously discussed?
2. **Conversation Coherence**: Do the responses build logically on prior \
   exchanges? Is there unnecessary repetition or contradiction?
3. **Completeness Across Turns**: Evaluate the final state of the \
   conversation thread as a whole. Information provided across multiple \
   turns counts toward completeness.
4. **Clarification Quality**: If the system asked for missing information, \
   evaluate whether those questions were relevant, specific, and well-structured. \
   Good clarification demonstrates domain expertise. However, a system that \
   provides a comprehensive answer with clearly stated assumptions is equally \
   valid. Score the final substantive quality, not the interaction style.
5. **Progressive Depth**: Does the conversation demonstrate deepening \
   engagement with the topic, or does the system restart from scratch \
   each turn?
"""


def _format_conversation_turns(
    user_prompts: Sequence[str],
    response_texts: Sequence[str],
) -> str:
    """Format a multi-turn conversation for the judge prompt."""
    parts: list[str] = []
    for i, (prompt, response) in enumerate(
        zip(user_prompts, response_texts), start=1
    ):
        parts.append(f"### Turn {i}")
        parts.append(f"**User:** {prompt}")
        parts.append(f"**System:** {response}")
        parts.append("")
    return "\n".join(parts)


def build_evaluation_prompt(
    dimension: RubricDimension,
    case_context: str,
    user_prompt: str,
    response_text: str,
    expertise_mode: str,
    code_output: str = "",
    follow_up_prompts: Sequence[str] = (),
    follow_up_responses: Sequence[str] = (),
) -> str:
    """Build the user message for the judge to evaluate one dimension.

    For multi-turn cases, pass ``follow_up_prompts`` and
    ``follow_up_responses`` to include the full conversation thread.
    """
    is_multi_turn = bool(follow_up_prompts)

    parts = [
        f"## Evaluation Dimension: {dimension.name}",
        f"**Description:** {dimension.description}",
        "",
        "## Scoring Anchors:",
        dimension.anchor_text(),
        "",
        f"## Case Context:\n{case_context}",
        f"\n## Expertise Mode: {expertise_mode}",
    ]

    if is_multi_turn:
        all_prompts = [user_prompt, *follow_up_prompts]
        all_responses = [response_text, *follow_up_responses]
        parts.append("\n## Conversation Thread:")
        parts.append(
            _format_conversation_turns(all_prompts, all_responses)
        )
        parts.append(MULTI_TURN_JUDGE_ADDENDUM)
    else:
        parts.append(f"\n## User Prompt:\n{user_prompt}")
        parts.append(f"\n## Response to Evaluate:\n{response_text}")

    if code_output:
        parts.append(f"\n## Code Output:\n```\n{code_output}\n```")

    parts.append(
        "\n## Your Evaluation:\n"
        "Score this response on the dimension above. "
        "Return JSON with score, reasoning, and evidence."
    )

    return "\n".join(parts)


def build_batch_evaluation_prompt(
    rubric: Rubric,
    case_context: str,
    user_prompt: str,
    response_text: str,
    expertise_mode: str,
    agent_type: str,
    code_output: str = "",
    follow_up_prompts: Sequence[str] = (),
    follow_up_responses: Sequence[str] = (),
) -> str:
    """Build a single prompt that scores ALL dimensions + overall quality.

    This replaces 9 separate API calls (8 dimensions + 1 overall) with
    a single call, reducing cost by ~80%.
    """
    is_multi_turn = bool(follow_up_prompts)

    parts: list[str] = [
        f"## Case Context:\n{case_context}",
        f"\n## Expertise Mode: {expertise_mode}",
        f"\n## Agent Type: {agent_type}",
    ]

    if is_multi_turn:
        all_prompts = [user_prompt, *follow_up_prompts]
        all_responses = [response_text, *follow_up_responses]
        parts.append("\n## Conversation Thread:")
        parts.append(
            _format_conversation_turns(all_prompts, all_responses)
        )
        parts.append(MULTI_TURN_JUDGE_ADDENDUM)
    else:
        parts.append(f"\n## User Prompt:\n{user_prompt}")
        parts.append(f"\n## Response to Evaluate:\n{response_text}")

    if code_output:
        parts.append(f"\n## Code Output:\n```\n{code_output}\n```")

    parts.append("\n---\n## Dimensions to Score:\n")
    for dim in rubric.dimensions:
        code_note = ""
        if dim.dimension_id in ("B3", "B8") and not code_output:
            code_note = " (No code output available -- score based on code in the response text)"
        parts.append(f"### {dim.dimension_id}: {dim.name}{code_note}")
        parts.append(f"**Description:** {dim.description}")
        parts.append("**Anchors:**")
        parts.append(dim.anchor_text())
        parts.append("")

    parts.append(
        "### Overall Quality\n"
        f"Evaluate the overall quality of this {agent_type} response on a 1-5 scale:\n"
        "1 = Poor: Incorrect, unhelpful, or potentially harmful advice\n"
        "2 = Below Average: Partially correct but with significant gaps or errors\n"
        "3 = Adequate: Correct basic approach but lacking depth or nuance\n"
        "4 = Good: Accurate, well-structured, and actionable advice\n"
        "5 = Excellent: Comprehensive, accurate, pedagogically excellent, and "
        "actionable -- whether delivered in one turn or through a multi-turn exchange"
    )

    parts.append(
        "\n---\n## Your Evaluation:\n"
        "Score ALL dimensions above plus the overall quality. "
        "Return a single JSON object with \"dimensions\" array and \"overall\" object."
    )

    return "\n".join(parts)


def build_overall_quality_prompt(
    case_context: str,
    user_prompt: str,
    response_text: str,
    expertise_mode: str,
    agent_type: str,
    follow_up_prompts: Sequence[str] = (),
    follow_up_responses: Sequence[str] = (),
) -> str:
    """Build prompt for overall quality assessment (1-5)."""
    is_multi_turn = bool(follow_up_prompts)

    if is_multi_turn:
        all_prompts = [user_prompt, *follow_up_prompts]
        all_responses = [response_text, *follow_up_responses]
        conversation_block = _format_conversation_turns(
            all_prompts, all_responses
        )
        multi_turn_note = MULTI_TURN_JUDGE_ADDENDUM
    else:
        conversation_block = ""
        multi_turn_note = ""

    if is_multi_turn:
        response_section = (
            f"## Conversation Thread:\n{conversation_block}"
        )
    else:
        response_section = f"## Response to Evaluate:\n{response_text}"

    return f"""\
## Overall Quality Assessment

Evaluate the overall quality of this {agent_type} response on a 1-5 scale:

1 = Poor: Incorrect, unhelpful, or potentially harmful advice
2 = Below Average: Partially correct but with significant gaps or errors
3 = Adequate: Correct basic approach but lacking depth or nuance
4 = Good: Accurate, well-structured, and actionable advice
5 = Excellent: Comprehensive, accurate, pedagogically excellent, and \
actionable -- whether delivered in one turn or through a multi-turn exchange

## Case Context:
{case_context}

## Expertise Mode: {expertise_mode}

{response_section}
{multi_turn_note}
## Your Evaluation:
Return JSON with score, reasoning, and evidence.
"""
