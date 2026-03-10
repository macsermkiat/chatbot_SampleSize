"""Store and load collected responses as JSON files."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from evaluation.collectors.chatbot_collector import CollectedResponse
from evaluation.config import EvalConfig


def save_responses(
    responses: list[CollectedResponse],
    system_id: str,
    config: EvalConfig,
) -> Path:
    """Save collected responses to a JSON file."""
    output_dir = Path(config.raw_responses_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    filepath = output_dir / f"{system_id}_responses.json"
    data = [asdict(r) for r in responses]

    filepath.write_text(json.dumps(data, indent=2, default=str))
    return filepath


def load_responses(system_id: str, config: EvalConfig) -> list[CollectedResponse]:
    """Load previously collected responses from JSON."""
    filepath = Path(config.raw_responses_dir) / f"{system_id}_responses.json"

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


def get_responses_by_case(
    responses: list[CollectedResponse],
) -> dict[str, list[CollectedResponse]]:
    """Group responses by case_id."""
    grouped: dict[str, list[CollectedResponse]] = {}
    for r in responses:
        grouped.setdefault(r.case_id, []).append(r)
    return grouped
