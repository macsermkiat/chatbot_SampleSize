"""Simulated user that answers chatbot clarification questions dynamically.

The chatbot often asks clarification questions before giving substantive
answers. This module classifies chatbot responses (routing / clarification /
substantive) and generates contextual user replies using gpt-5-nano, drawing
on the test case ground truth to provide realistic answers.
"""

from __future__ import annotations

import logging
import re
import time
import uuid
from typing import Literal

import httpx
from openai import AsyncOpenAI

from evaluation.collectors.chatbot_collector import (
    CollectedResponse,
    _send_and_collect_sse,
)
from evaluation.config import EvalConfig
from evaluation.test_cases.schema import TestCase

logger = logging.getLogger(__name__)

ResponseType = Literal["routing", "clarification", "substantive"]

_ROUTING_PATTERNS: tuple[re.Pattern[str], ...] = tuple(
    re.compile(p, re.IGNORECASE)
    for p in (
        r"\broute\b",
        r"\brouting\b",
        r"\btransfer\b",
        r"\bforwarding\b",
        r"\bdirect you to\b",
        r"\bmethodology agent\b",
        r"\bbiostatistics agent\b",
        r"\bresearch gap\b",
        r"\blet me connect you\b",
        r"\bi'?ll pass this to\b",
    )
)

_CLARIFICATION_PATTERNS: tuple[re.Pattern[str], ...] = tuple(
    re.compile(p, re.IGNORECASE)
    for p in (
        r"\bcould you clarify\b",
        r"\bcan you provide\b",
        r"\bwhat is\b",
        r"\bcould you tell me\b",
        r"\bneed more information\b",
        r"\bplease specify\b",
        r"\bhelp me understand\b",
        r"\bbefore I can\b",
        r"\bin order to\b",
    )
)

_SIMULATED_USER_MODEL = "gpt-5-nano"
_MAX_CONVERSATION_TURNS = 10


def classify_response(text: str) -> ResponseType:
    """Classify a chatbot response as routing, clarification, or substantive.

    Uses fast heuristic patterns first. Falls back to a simple length/question
    heuristic when patterns are ambiguous (no LLM call for classification to
    keep latency low).
    """
    stripped = text.strip()
    if not stripped:
        return "routing"

    # Check routing patterns
    routing_hits = sum(1 for p in _ROUTING_PATTERNS if p.search(stripped))
    if routing_hits >= 1 and len(stripped) < 300:
        return "routing"

    # Long responses (>1000 chars) are almost always substantive even if
    # they contain clarification questions at the end.
    if len(stripped) > 1000:
        return "substantive"

    # Check clarification patterns
    clarification_hits = sum(
        1 for p in _CLARIFICATION_PATTERNS if p.search(stripped)
    )
    has_question_mark = "?" in stripped

    if clarification_hits >= 1 and has_question_mark:
        return "clarification"

    # Short responses with a question mark are likely clarification
    if has_question_mark and len(stripped) < 500 and clarification_hits == 0:
        # Count sentences -- if mostly questions, treat as clarification
        sentences = [s.strip() for s in re.split(r"[.!?]+", stripped) if s.strip()]
        questions = sum(1 for s in stripped.split("?") if s.strip())
        if questions > len(sentences) / 2:
            return "clarification"

    # Long responses with routing keywords may still be routing
    if routing_hits >= 2:
        return "routing"

    # Default: anything substantial enough is a real answer
    if len(stripped) > 200:
        return "substantive"

    # Short, ambiguous text without clear patterns -- treat as clarification
    # if it has a question mark, otherwise routing
    if has_question_mark:
        return "clarification"

    return "routing"


def _build_ground_truth_context(case: TestCase) -> str:
    """Extract ground truth information into a plain-text context block.

    The simulated user draws on this to answer the chatbot's questions
    as if they were a researcher who knows their own study parameters.
    """
    parts: list[str] = []

    parts.append(f"Clinical context: {case.clinical_context}")
    parts.append(f"Medical specialty: {case.specialty}")
    parts.append(f"Target agent: {case.agent_target}")

    if case.methodology_ground_truth is not None:
        gt = case.methodology_ground_truth
        parts.append(f"Study design: {gt.study_design}")
        if gt.pico_elements:
            pico_lines = [f"  {k}: {v}" for k, v in gt.pico_elements.items()]
            parts.append("PICO elements:\n" + "\n".join(pico_lines))
        if gt.biases_to_identify:
            parts.append(f"Known biases: {', '.join(gt.biases_to_identify)}")
        if gt.equator_guideline:
            parts.append(f"EQUATOR guideline: {gt.equator_guideline}")
        if gt.causal_framework:
            parts.append(f"Causal framework: {gt.causal_framework}")
        if gt.ethical_considerations:
            parts.append(
                f"Ethical considerations: {', '.join(gt.ethical_considerations)}"
            )
        if gt.key_confounders:
            parts.append(f"Key confounders: {', '.join(gt.key_confounders)}")

    if case.biostatistics_ground_truth is not None:
        gt = case.biostatistics_ground_truth
        parts.append(f"Statistical test: {gt.correct_statistical_test}")
        if gt.required_parameters:
            param_lines = [
                f"  {k}: {v}" for k, v in gt.required_parameters.items()
            ]
            parts.append("Study parameters:\n" + "\n".join(param_lines))
        if gt.required_assumptions:
            parts.append(
                f"Assumptions: {', '.join(gt.required_assumptions)}"
            )
        if gt.sample_size_range != (0, 0):
            lo, hi = gt.sample_size_range
            parts.append(f"Expected sample size range: {lo} - {hi} per group")
        if gt.formula_name:
            parts.append(f"Formula: {gt.formula_name}")

    return "\n".join(parts)


async def generate_user_response(
    case: TestCase,
    chatbot_question: str,
    conversation_history: list[dict[str, str]],
    config: EvalConfig,
) -> str:
    """Generate a simulated user reply to a chatbot clarification question.

    Uses gpt-5-nano to produce a brief, natural response that answers the
    chatbot's question using information from the test case ground truth.
    """
    ground_truth_context = _build_ground_truth_context(case)

    system_prompt = (
        "You are simulating a medical researcher who is asking a chatbot "
        "for help with study design. The chatbot has asked you a clarification "
        "question. Answer it concisely and naturally, as a real researcher would.\n\n"
        "Use ONLY the following study details to inform your answer. Do not "
        "invent information beyond what is provided.\n\n"
        f"--- Study Details ---\n{ground_truth_context}\n--- End ---\n\n"
        "Guidelines:\n"
        "- Answer directly and briefly (2-4 sentences max)\n"
        "- Use a natural, conversational tone\n"
        "- Provide specific numbers and parameters when asked\n"
        "- Do not volunteer information that was not asked for\n"
        "- Do not mention that you are a simulated user"
    )

    messages: list[dict[str, str]] = [{"role": "system", "content": system_prompt}]

    # Include recent conversation history for context (last 6 exchanges max)
    recent_history = conversation_history[-6:]
    messages.extend(recent_history)

    # Add the chatbot's clarification as the latest assistant message
    messages.append({"role": "assistant", "content": chatbot_question})

    client = AsyncOpenAI(api_key=config.openai_api_key)

    try:
        completion = await client.chat.completions.create(
            model=config.simulated_user_model,
            messages=messages,
            max_completion_tokens=256,
        )
        response = completion.choices[0].message.content or ""
        logger.debug(
            "Simulated user response for %s: %s",
            case.case_id,
            response[:100],
        )
        return response.strip()
    except Exception as exc:
        logger.error(
            "Failed to generate simulated user response for %s: %s",
            case.case_id,
            exc,
        )
        raise


async def run_conversation_loop(
    case: TestCase,
    config: EvalConfig,
) -> list[CollectedResponse]:
    """Orchestrate a multi-turn conversation with the chatbot.

    Sends the initial prompt, then classifies each response. If the chatbot
    asks for clarification, a simulated user response is generated and sent
    back. Routing messages are skipped. The loop ends when a substantive
    response is received or the turn limit is reached.

    Returns all CollectedResponse objects gathered during the conversation.
    """
    session_id = f"eval-sim-{case.case_id}-{uuid.uuid4().hex[:8]}"
    responses: list[CollectedResponse] = []
    conversation_history: list[dict[str, str]] = []
    current_prompt = case.prompt

    client_timeout = httpx.Timeout(
        connect=10.0,
        read=float(config.chatbot_timeout_seconds),
        write=10.0,
        pool=10.0,
    )
    async with httpx.AsyncClient(timeout=client_timeout) as client:
        # Create session
        try:
            await client.post(
                config.chatbot_session_url,
                json={"session_id": session_id},
            )
        except httpx.HTTPError:
            pass  # Session endpoint may auto-create

        for turn_num in range(1, _MAX_CONVERSATION_TURNS + 1):
            logger.info(
                "Case %s turn %d: sending prompt (%d chars)",
                case.case_id,
                turn_num,
                len(current_prompt),
            )

            start_time = time.monotonic()
            raw_response = await _send_and_collect_sse(
                client=client,
                url=config.chatbot_api_url,
                payload={
                    "message": current_prompt,
                    "session_id": session_id,
                    "expertise_level": case.expertise_mode,
                },
                timeout=config.chatbot_timeout_seconds,
            )
            elapsed_ms = (time.monotonic() - start_time) * 1000

            response_text = raw_response["text"]
            collected = CollectedResponse(
                case_id=case.case_id,
                system_id="chatbot",
                session_id=session_id,
                turn_number=turn_num,
                prompt=current_prompt,
                response_text=response_text,
                code_output=raw_response["code"],
                execution_result=raw_response["execution_result"],
                phase_transitions=tuple(raw_response["phases"]),
                latency_ms=elapsed_ms,
                expertise_mode=case.expertise_mode,
            )
            responses.append(collected)

            response_type = classify_response(response_text)
            logger.info(
                "Case %s turn %d: classified as %s (%d chars)",
                case.case_id,
                turn_num,
                response_type,
                len(response_text),
            )

            if response_type == "substantive":
                logger.info(
                    "Case %s: substantive response received at turn %d",
                    case.case_id,
                    turn_num,
                )
                break

            if response_type == "routing":
                # Routing messages are transitional; continue waiting for
                # the next response without injecting a user message.
                conversation_history.append(
                    {"role": "assistant", "content": response_text}
                )
                # Re-send the same prompt to nudge past routing
                continue

            # response_type == "clarification"
            conversation_history.append(
                {"role": "user", "content": current_prompt}
            )
            conversation_history.append(
                {"role": "assistant", "content": response_text}
            )

            simulated_reply = await generate_user_response(
                case=case,
                chatbot_question=response_text,
                conversation_history=conversation_history,
                config=config,
            )

            logger.info(
                "Case %s turn %d: simulated user reply: %s",
                case.case_id,
                turn_num,
                simulated_reply[:80],
            )

            current_prompt = simulated_reply
            conversation_history.append(
                {"role": "user", "content": simulated_reply}
            )

        else:
            logger.warning(
                "Case %s: reached max turns (%d) without substantive response",
                case.case_id,
                _MAX_CONVERSATION_TURNS,
            )

    return responses
