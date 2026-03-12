"""Collect responses from the local chatbot API (SSE streaming)."""

from __future__ import annotations

import json
import logging
import time
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path

import httpx

from evaluation.config import EvalConfig
from evaluation.test_cases.schema import TestCase

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CollectedResponse:
    """A single response collected from a system."""

    case_id: str
    system_id: str
    session_id: str
    turn_number: int
    prompt: str
    response_text: str
    code_output: str
    execution_result: str
    phase_transitions: tuple[str, ...]
    latency_ms: float
    expertise_mode: str


async def collect_chatbot_response(
    case: TestCase, config: EvalConfig
) -> list[CollectedResponse]:
    """Send a test case to the chatbot and collect all turn responses."""
    session_id = f"eval-{case.case_id}-{uuid.uuid4().hex[:8]}"
    responses: list[CollectedResponse] = []

    all_prompts = [case.prompt, *case.follow_up_prompts]

    async with httpx.AsyncClient(timeout=config.chatbot_timeout_seconds) as client:
        # Create session
        try:
            await client.post(
                config.chatbot_session_url,
                json={"session_id": session_id},
            )
        except httpx.HTTPError:
            pass  # Session endpoint may auto-create

        for turn_num, prompt in enumerate(all_prompts, start=1):
            start_time = time.monotonic()
            response = await _send_and_collect_sse(
                client=client,
                url=config.chatbot_api_url,
                payload={
                    "message": prompt,
                    "session_id": session_id,
                    "expertise_level": case.expertise_mode,
                },
                timeout=config.chatbot_timeout_seconds,
            )
            elapsed_ms = (time.monotonic() - start_time) * 1000

            responses.append(
                CollectedResponse(
                    case_id=case.case_id,
                    system_id="chatbot",
                    session_id=session_id,
                    turn_number=turn_num,
                    prompt=prompt,
                    response_text=response["text"],
                    code_output=response["code"],
                    execution_result=response["execution_result"],
                    phase_transitions=tuple(response["phases"]),
                    latency_ms=elapsed_ms,
                    expertise_mode=case.expertise_mode,
                )
            )

    return responses


async def _send_and_collect_sse(
    client: httpx.AsyncClient,
    url: str,
    payload: dict,
    timeout: int,
) -> dict:
    """Send a request and parse the SSE stream into structured data."""
    text_parts: list[str] = []
    code_parts: list[str] = []
    execution_result = ""
    phases: list[str] = []

    # Use explicit timeout: generous read timeout for SSE (server sends
    # keep-alive pings), but tighter connect/write/pool timeouts.
    stream_timeout = httpx.Timeout(
        connect=10.0,
        read=float(timeout),
        write=10.0,
        pool=10.0,
    )

    async with client.stream(
        "POST",
        url,
        json=payload,
        timeout=stream_timeout,
        headers={"Accept": "text/event-stream"},
    ) as stream:
        current_event = ""
        async for line in stream.aiter_lines():
            line = line.strip()
            if not line:
                current_event = ""
                continue

            if line.startswith("event:"):
                current_event = line[6:].strip()
                if current_event == "done":
                    break
                continue

            if line.startswith("data:"):
                data_str = line[5:].strip()
                try:
                    data = json.loads(data_str)
                except (json.JSONDecodeError, ValueError):
                    data = {"content": data_str}

                if current_event == "message" or not current_event:
                    content = data.get("content", "")
                    if content:
                        text_parts.append(content)

                elif current_event == "phase_change":
                    phase = data.get("phase", "")
                    if phase:
                        phases.append(phase)

                elif current_event == "code":
                    script = data.get("script", "")
                    if script:
                        code_parts.append(script)

                elif current_event == "execution_result":
                    execution_result = data.get("stdout", "")

    return {
        "text": "".join(text_parts),
        "code": "\n".join(code_parts),
        "execution_result": execution_result,
        "phases": phases,
    }


def _save_incremental(
    responses: list[CollectedResponse], config: EvalConfig
) -> None:
    """Save responses to disk after each case for crash resilience."""
    output_dir = Path(config.raw_responses_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    filepath = output_dir / "chatbot_responses.json"
    data = [asdict(r) for r in responses]
    filepath.write_text(json.dumps(data, indent=2, default=str))


def _load_existing(config: EvalConfig) -> list[CollectedResponse]:
    """Load previously collected responses for resume support."""
    filepath = Path(config.raw_responses_dir) / "chatbot_responses.json"
    if not filepath.exists():
        return []
    data = json.loads(filepath.read_text())
    return [
        CollectedResponse(
            case_id=item["case_id"],
            system_id=item["system_id"],
            session_id=item["session_id"],
            turn_number=item["turn_number"],
            prompt=item["prompt"],
            response_text=item["response_text"],
            code_output=item["code_output"],
            execution_result=item.get("execution_result", ""),
            phase_transitions=tuple(item.get("phase_transitions", [])),
            latency_ms=item["latency_ms"],
            expertise_mode=item["expertise_mode"],
        )
        for item in data
    ]


async def collect_all_chatbot_responses(
    cases: list[TestCase], config: EvalConfig
) -> list[CollectedResponse]:
    """Collect responses for all test cases sequentially.

    Saves after each case for crash resilience. Resumes from where it
    left off if valid partial results exist on disk.
    """
    existing = _load_existing(config)
    completed_cases = {
        r.case_id
        for r in existing
        if r.response_text and "[ERROR]" not in r.response_text
    }

    if completed_cases:
        logger.info(
            "Resuming: %d cases already collected, skipping them",
            len(completed_cases),
        )

    all_responses: list[CollectedResponse] = list(existing) if completed_cases else []

    for i, case in enumerate(cases, 1):
        if case.case_id in completed_cases:
            logger.info(
                "Skipping case %d/%d: %s (already collected)", i, len(cases), case.case_id
            )
            continue

        logger.info("Collecting case %d/%d: %s", i, len(cases), case.case_id)
        try:
            if config.use_simulated_user:
                from evaluation.collectors.simulated_user import run_conversation_loop

                responses = await run_conversation_loop(case, config)
            else:
                responses = await collect_chatbot_response(case, config)
            all_responses.extend(responses)
            for r in responses:
                logger.info(
                    "  Turn %d: %d chars response", r.turn_number, len(r.response_text)
                )
        except Exception as exc:
            all_responses.append(
                CollectedResponse(
                    case_id=case.case_id,
                    system_id="chatbot",
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
        _save_incremental(all_responses, config)

    return all_responses
