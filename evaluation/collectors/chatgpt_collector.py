"""Collect responses from GPT-5 via OpenAI API (vanilla, no system prompt)."""

from __future__ import annotations

import time

from openai import AsyncOpenAI

from evaluation.collectors.chatbot_collector import CollectedResponse
from evaluation.config import EvalConfig
from evaluation.test_cases.schema import TestCase


async def collect_gpt5_response(
    case: TestCase, config: EvalConfig
) -> list[CollectedResponse]:
    """Send test case prompts to GPT-5 and collect responses.

    Mimics the vanilla ChatGPT experience:
    - No system prompt
    - No tools or code execution
    - Default temperature (0.7)
    """
    client = AsyncOpenAI(api_key=config.openai_api_key)
    responses: list[CollectedResponse] = []
    conversation: list[dict] = []

    all_prompts = [case.prompt, *case.follow_up_prompts]

    for turn_num, prompt in enumerate(all_prompts, start=1):
        conversation.append({"role": "user", "content": prompt})

        start_time = time.monotonic()

        # GPT-5 only supports default temperature (1) and uses
        # max_completion_tokens instead of max_tokens.
        create_kwargs: dict = {
            "model": config.comparison_model,
            "messages": conversation,
            "max_completion_tokens": 16384,
        }
        # Only pass temperature if the model supports it (GPT-5 does not)
        if not config.comparison_model.startswith("gpt-5"):
            create_kwargs["temperature"] = config.comparison_temperature

        completion = await client.chat.completions.create(**create_kwargs)

        elapsed_ms = (time.monotonic() - start_time) * 1000
        response_text = completion.choices[0].message.content or ""

        conversation.append({"role": "assistant", "content": response_text})

        # Extract any code blocks from the response
        code_output = _extract_code_blocks(response_text)

        responses.append(
            CollectedResponse(
                case_id=case.case_id,
                system_id="gpt5",
                session_id=f"gpt5-{case.case_id}",
                turn_number=turn_num,
                prompt=prompt,
                response_text=response_text,
                code_output=code_output,
                execution_result="",  # GPT-5 does not execute code
                phase_transitions=(),
                latency_ms=elapsed_ms,
                expertise_mode=case.expertise_mode,
            )
        )

    return responses


def _extract_code_blocks(text: str) -> str:
    """Extract fenced code blocks from markdown text."""
    blocks: list[str] = []
    in_block = False
    current_block: list[str] = []

    for line in text.split("\n"):
        if line.strip().startswith("```"):
            if in_block:
                blocks.append("\n".join(current_block))
                current_block = []
                in_block = False
            else:
                in_block = True
        elif in_block:
            current_block.append(line)

    return "\n\n".join(blocks)


async def collect_all_gpt5_responses(
    cases: list[TestCase], config: EvalConfig
) -> list[CollectedResponse]:
    """Collect GPT-5 responses for all test cases sequentially."""
    all_responses: list[CollectedResponse] = []
    for case in cases:
        try:
            responses = await collect_gpt5_response(case, config)
            all_responses.extend(responses)
        except Exception as exc:
            all_responses.append(
                CollectedResponse(
                    case_id=case.case_id,
                    system_id="gpt5",
                    session_id="error",
                    turn_number=1,
                    prompt=case.prompt,
                    response_text=f"[ERROR] {exc}",
                    code_output="",
                    execution_result="",
                    phase_transitions=(),
                    latency_ms=0,
                    expertise_mode=case.expertise_mode,
                )
            )
    return all_responses
