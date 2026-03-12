"""Re-judge responses via Anthropic Batch API (50% cost savings).

Supports judging both systems with multiple runs, or chatbot-only single run.

Usage:
    cd chatbot_SampleSize
    set -a && source backend/.env && set +a
    backend/.venv/bin/python -m evaluation.batch_rejudge submit --both --runs 3
    backend/.venv/bin/python -m evaluation.batch_rejudge submit              # chatbot only, 1 run
    backend/.venv/bin/python -m evaluation.batch_rejudge poll <batch_id>
    backend/.venv/bin/python -m evaluation.batch_rejudge results <batch_id>
"""

from __future__ import annotations

import argparse
import json
import logging
import time
from pathlib import Path

from anthropic import Anthropic

from evaluation.config import EvalConfig
from evaluation.runner import load_test_cases
from evaluation.collectors.response_store import (
    get_responses_by_case,
    load_responses,
)
from evaluation.llm_judge.blinding import create_blinded_pairs, BlindedPair
from evaluation.llm_judge.judge_prompt import (
    JUDGE_BATCH_SYSTEM_PROMPT,
    build_batch_evaluation_prompt,
)
from evaluation.llm_judge.judge_runner import (
    _clamp_score,
    _parse_batch_dimensions,
    _save_results,
)
from evaluation.rubrics.schema import EvaluationResult, Rubric
from evaluation.rubrics.methodology_rubric import METHODOLOGY_RUBRIC
from evaluation.rubrics.biostatistics_rubric import BIOSTATISTICS_RUBRIC
from evaluation.test_cases.schema import TestCase

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

BATCH_STATE_FILE = "evaluation/output/judge_results/batch_state.json"


def _parse_judge_json(text: str, custom_id: str) -> dict:
    """Parse judge JSON response, handling truncation and markdown fences."""
    json_text = text.strip()

    # Strip markdown fences
    if "```" in json_text:
        json_text = json_text.split("```")[1]
        if json_text.startswith("json"):
            json_text = json_text[4:]

    # Try direct parse
    try:
        return json.loads(json_text)
    except json.JSONDecodeError:
        pass

    # Truncated JSON: try to repair by extracting what we can
    # Extract dimension scores that are complete
    import re
    dimensions = []
    for m in re.finditer(
        r'\{\s*"dimension_id"\s*:\s*"([^"]+)"\s*,\s*"score"\s*:\s*(\d+)',
        json_text,
    ):
        dimensions.append({
            "dimension_id": m.group(1),
            "score": int(m.group(2)),
            "reasoning": "truncated",
            "evidence": "",
        })

    # Extract overall score if present
    overall_match = re.search(
        r'"overall"\s*:\s*\{[^}]*"score"\s*:\s*(\d+)', json_text
    )
    overall_score = int(overall_match.group(1)) if overall_match else 3

    if dimensions:
        logger.info(
            "Recovered %d dimensions from truncated response for %s",
            len(dimensions), custom_id,
        )
        return {
            "dimensions": dimensions,
            "overall": {"score": overall_score, "reasoning": "truncated response"},
        }

    logger.warning("Failed to parse JSON for %s", custom_id)
    return {
        "dimensions": [],
        "overall": {"score": 3, "reasoning": "Parse error"},
    }


def _build_batch_requests(
    pairs: list[BlindedPair],
    cases: list[TestCase],
    config: EvalConfig,
    both_systems: bool = False,
    num_runs: int = 1,
    only_cases: set[str] | None = None,
) -> list[dict]:
    """Build batch request payloads.

    Args:
        both_systems: If True, judge both systems. Otherwise chatbot only.
        num_runs: Number of judge runs per response (1-3).
        only_cases: If set, only include these case IDs.
    """
    case_lookup = {c.case_id: c for c in cases}
    requests = []

    for pair in pairs:
        if only_cases and pair.case_id not in only_cases:
            continue
        case = case_lookup.get(pair.case_id)
        if not case:
            continue

        rubric = BIOSTATISTICS_RUBRIC if case.agent_target == "biostatistics" else METHODOLOGY_RUBRIC

        # Determine which responses to judge
        responses_to_judge = []
        if both_systems:
            responses_to_judge = [pair.system_a, pair.system_b]
        else:
            for label, identity in pair.label_to_identity.items():
                if identity == "chatbot":
                    resp = pair.system_a if pair.system_a.blinded_label == label else pair.system_b
                    responses_to_judge = [resp]
                    break

        for response in responses_to_judge:
            prompt = build_batch_evaluation_prompt(
                rubric=rubric,
                case_context=case.clinical_context,
                user_prompt=case.prompt,
                response_text=response.text,
                expertise_mode=case.expertise_mode,
                agent_type=case.agent_target,
                code_output=response.code,
            )

            for run in range(1, num_runs + 1):
                # custom_id must match ^[a-zA-Z0-9_-]{1,64}$
                custom_id = f"{case.case_id}--{response.blinded_label}--run{run}--{rubric.rubric_id}"

                requests.append({
                    "custom_id": custom_id,
                    "params": {
                        "model": config.judge_model,
                        "max_tokens": 4096,
                        "temperature": config.judge_temperature,
                        "system": [
                            {
                                "type": "text",
                                "text": JUDGE_BATCH_SYSTEM_PROMPT,
                                "cache_control": {"type": "ephemeral"},
                            }
                        ],
                        "messages": [{"role": "user", "content": prompt}],
                    },
                })

    return requests


def submit_batch(
    config: EvalConfig,
    both_systems: bool = False,
    num_runs: int = 1,
    only_cases: set[str] | None = None,
) -> str:
    """Submit batch of judge requests."""
    cases = load_test_cases()

    chatbot_responses = load_responses("chatbot", config)
    gpt5_responses = load_responses("gpt5", config)
    chatbot_by_case = get_responses_by_case(chatbot_responses)
    gpt5_by_case = get_responses_by_case(gpt5_responses)

    pairs = create_blinded_pairs(chatbot_by_case, gpt5_by_case, seed=config.random_seed)
    logger.info("Created %d blinded pairs", len(pairs))

    requests = _build_batch_requests(pairs, cases, config, both_systems, num_runs, only_cases)
    mode = "both systems" if both_systems else "chatbot only"
    cases_desc = f", cases={sorted(only_cases)}" if only_cases else ""
    logger.info("Built %d batch requests (%s, %d run(s)%s)", len(requests), mode, num_runs, cases_desc)

    client = Anthropic(api_key=config.anthropic_api_key)
    batch = client.messages.batches.create(requests=requests)

    logger.info("Batch submitted: %s (status: %s)", batch.id, batch.processing_status)

    state = {
        "batch_id": batch.id,
        "status": batch.processing_status,
        "both_systems": both_systems,
        "num_runs": num_runs,
        "n_requests": len(requests),
        "only_cases": sorted(only_cases) if only_cases else None,
    }
    state_path = Path(BATCH_STATE_FILE)
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(json.dumps(state, indent=2))

    print(f"\nBatch ID: {batch.id}")
    print(f"Requests: {len(requests)} ({mode}, {num_runs} run(s){cases_desc})")
    print(f"Status: {batch.processing_status}")
    print(f"\nPoll with:  backend/.venv/bin/python -m evaluation.batch_rejudge poll {batch.id}")
    print(f"Results:    backend/.venv/bin/python -m evaluation.batch_rejudge results {batch.id}")

    return batch.id


def poll_batch(batch_id: str, config: EvalConfig) -> str:
    """Check batch processing status."""
    client = Anthropic(api_key=config.anthropic_api_key)
    batch = client.messages.batches.retrieve(batch_id)

    print(f"Batch: {batch.id}")
    print(f"Status: {batch.processing_status}")
    print(f"Counts: {batch.request_counts}")

    return batch.processing_status


def collect_results(batch_id: str, config: EvalConfig) -> None:
    """Collect batch results and save as judge_results.json."""
    client = Anthropic(api_key=config.anthropic_api_key)

    # Check status first
    batch = client.messages.batches.retrieve(batch_id)
    if batch.processing_status != "ended":
        print(f"Batch not ready: {batch.processing_status}")
        print(f"Counts: {batch.request_counts}")
        return

    # Load batch state to know if this was both-systems or chatbot-only
    state_path = Path(BATCH_STATE_FILE)
    both_systems = False
    only_cases = None
    if state_path.exists():
        state = json.loads(state_path.read_text())
        both_systems = state.get("both_systems", False)
        only_cases = set(state["only_cases"]) if state.get("only_cases") else None

    # Parse all results from batch
    new_results: list[EvaluationResult] = []
    succeeded = 0
    failed = 0

    for result in client.messages.batches.results(batch_id):
        if result.result.type != "succeeded":
            logger.warning("Request %s failed: %s", result.custom_id, result.result.type)
            failed += 1
            continue

        succeeded += 1
        parts = result.custom_id.split("--")
        case_id, system_id, run_label, rubric_id = parts[0], parts[1], parts[2], parts[3]
        judge_run = int(run_label.replace("run", ""))

        rubric = BIOSTATISTICS_RUBRIC if rubric_id == BIOSTATISTICS_RUBRIC.rubric_id else METHODOLOGY_RUBRIC

        response_text = result.result.message.content[0].text.strip()
        result_data = _parse_judge_json(response_text, result.custom_id)

        dimension_scores = _parse_batch_dimensions(result_data, rubric)
        overall = result_data.get("overall", {})

        new_results.append(
            EvaluationResult(
                case_id=case_id,
                system_id=system_id,
                judge_run=judge_run,
                rubric_id=rubric_id,
                dimension_scores=dimension_scores,
                overall_quality=_clamp_score(overall.get("score", 3)),
                overall_reasoning=overall.get("reasoning", ""),
            )
        )

    logger.info("Batch results: %d succeeded, %d failed", succeeded, failed)

    new_case_ids = {r.case_id for r in new_results}

    if only_cases:
        # Partial update: merge new results into existing, replacing only affected case+system pairs
        judge_path = Path(config.judge_results_dir) / "judge_results.json"
        existing = []
        if judge_path.exists():
            existing = [EvaluationResult.model_validate(r) for r in json.loads(judge_path.read_text())]

        # Build set of (case_id, system_id) pairs being replaced
        replaced_pairs = {(r.case_id, r.system_id) for r in new_results}

        # Keep existing results that are NOT being replaced
        kept = [
            r for r in existing
            if (r.case_id, r.system_id) not in replaced_pairs
        ]
        combined = kept + new_results
        _save_results(combined, config)

        logger.info("Patched %d cases: kept %d existing + %d new = %d total",
                     len(new_case_ids), len(kept), len(new_results), len(combined))
        print(f"\nResults patched (cases: {sorted(new_case_ids)}):")
        print(f"  Kept:    {len(kept)}")
        print(f"  New:     {len(new_results)}")
        print(f"  Total:   {len(combined)}")

    elif both_systems:
        # Full replacement -- batch contains both systems
        _save_results(new_results, config)
        logger.info("Saved %d results (full replacement)", len(new_results))

        by_system: dict[str, int] = {}
        for r in new_results:
            by_system[r.system_id] = by_system.get(r.system_id, 0) + 1
        n_cases = len(new_case_ids)

        print(f"\nResults collected (both systems):")
        for sid, count in sorted(by_system.items()):
            print(f"  {sid}: {count} results")
        print(f"  Cases: {n_cases}")
        print(f"  Total saved: {len(new_results)}")
    else:
        # Chatbot-only: merge with existing GPT-5 results
        chatbot_responses = load_responses("chatbot", config)
        gpt5_responses = load_responses("gpt5", config)
        chatbot_by_case = get_responses_by_case(chatbot_responses)
        gpt5_by_case = get_responses_by_case(gpt5_responses)
        pairs = create_blinded_pairs(chatbot_by_case, gpt5_by_case, seed=config.random_seed)

        identity_map = {p.case_id: dict(p.label_to_identity) for p in pairs}

        judge_path = Path(config.judge_results_dir) / "judge_results.json"
        existing = []
        if judge_path.exists():
            existing = [EvaluationResult.model_validate(r) for r in json.loads(judge_path.read_text())]

        gpt5_results = [
            r for r in existing
            if identity_map.get(r.case_id, {}).get(r.system_id) == "gpt5"
        ]
        logger.info("Kept %d GPT-5 results", len(gpt5_results))

        combined = gpt5_results + new_results
        _save_results(combined, config)
        logger.info("Saved %d combined results", len(combined))

        print(f"\nResults collected (chatbot only):")
        print(f"  GPT-5 kept:    {len(gpt5_results)}")
        print(f"  Chatbot new:   {len(new_results)}")
        print(f"  Total saved:   {len(combined)}")

    print(f"\nNow run analysis:")
    print(f"  PYTHONPATH=. backend/.venv/bin/python -m evaluation.runner analyze")


def main() -> None:
    parser = argparse.ArgumentParser(description="Batch judge via Anthropic Batch API")
    subparsers = parser.add_subparsers(dest="command", required=True)

    submit_parser = subparsers.add_parser("submit", help="Submit batch judge requests")
    submit_parser.add_argument("--both", action="store_true", help="Judge both systems (default: chatbot only)")
    submit_parser.add_argument("--runs", type=int, default=1, help="Judge runs per response (default: 1)")
    submit_parser.add_argument("--cases", nargs="+", help="Only judge specific case IDs")

    poll_parser = subparsers.add_parser("poll", help="Check batch status")
    poll_parser.add_argument("batch_id", help="Batch ID to check")

    results_parser = subparsers.add_parser("results", help="Collect results and save")
    results_parser.add_argument("batch_id", help="Batch ID to collect from")

    args = parser.parse_args()
    config = EvalConfig()

    if args.command == "submit":
        only = set(args.cases) if args.cases else None
        submit_batch(config, both_systems=args.both, num_runs=args.runs, only_cases=only)
    elif args.command == "poll":
        poll_batch(args.batch_id, config)
    elif args.command == "results":
        collect_results(args.batch_id, config)


if __name__ == "__main__":
    main()
