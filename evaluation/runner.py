"""Main orchestrator CLI for the evaluation pipeline (Phases 3-5).

Usage:
    python -m evaluation.runner collect --system chatbot
    python -m evaluation.runner collect --system gpt5
    python -m evaluation.runner collect --system both
    python -m evaluation.runner evaluate
    python -m evaluation.runner run-all
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path

from evaluation.config import EvalConfig
from evaluation.test_cases.schema import TestCase, TestCaseBank
from evaluation.rubrics.methodology_rubric import METHODOLOGY_RUBRIC
from evaluation.rubrics.biostatistics_rubric import BIOSTATISTICS_RUBRIC
from evaluation.collectors.chatbot_collector import collect_all_chatbot_responses
from evaluation.collectors.chatgpt_collector import collect_all_gpt5_responses
from evaluation.collectors.response_store import (
    get_responses_by_case,
    load_responses,
    save_responses,
)
from evaluation.auto_eval.test_checker import check_statistical_test
from evaluation.auto_eval.completeness_checker import check_completeness
from evaluation.auto_eval.code_validator import validate_code
from evaluation.llm_judge.blinding import create_blinded_pairs
from evaluation.llm_judge.judge_runner import run_full_evaluation

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def load_test_cases() -> list[TestCase]:
    """Load all test cases from JSON files."""
    base = Path(__file__).parent / "test_cases"
    cases: list[TestCase] = []

    for filename in ("methodology_cases.json", "biostatistics_cases.json", "edge_cases.json"):
        filepath = base / filename
        if filepath.exists():
            raw = json.loads(filepath.read_text())
            # Handle both flat list and wrapped {"cases": [...]} format
            items = raw if isinstance(raw, list) else raw.get("cases", [])
            for item in items:
                cases.append(TestCase.model_validate(item))
            logger.info("Loaded %d cases from %s", len(items), filename)

    return cases


async def phase_collect(system: str, config: EvalConfig) -> None:
    """Phase 3: Collect responses from one or both systems."""
    cases = load_test_cases()
    logger.info("Loaded %d test cases total", len(cases))

    if system in ("chatbot", "both"):
        logger.info("Collecting chatbot responses...")
        chatbot_responses = await collect_all_chatbot_responses(cases, config)
        path = save_responses(chatbot_responses, "chatbot", config)
        logger.info("Saved %d chatbot responses to %s", len(chatbot_responses), path)

    if system in ("gpt5", "both"):
        logger.info("Collecting GPT-5 responses...")
        gpt5_responses = await collect_all_gpt5_responses(cases, config)
        path = save_responses(gpt5_responses, "gpt5", config)
        logger.info("Saved %d GPT-5 responses to %s", len(gpt5_responses), path)


def phase_auto_eval(config: EvalConfig) -> dict:
    """Phase 4: Run automated evaluation checks."""
    cases = load_test_cases()
    case_lookup = {c.case_id: c for c in cases}

    chatbot_responses = load_responses("chatbot", config)
    gpt5_responses = load_responses("gpt5", config)

    auto_results = {
        "test_checks": [],
        "completeness_checks": [],
        "code_validations": [],
    }

    for system_id, responses in [("chatbot", chatbot_responses), ("gpt5", gpt5_responses)]:
        for r in responses:
            case = case_lookup.get(r.case_id)
            if not case:
                continue

            # Test checker (biostatistics cases)
            if case.biostatistics_ground_truth:
                gt = case.biostatistics_ground_truth
                result = check_statistical_test(
                    case_id=r.case_id,
                    system_id=system_id,
                    response_text=r.response_text,
                    expected_test=gt.correct_statistical_test,
                    accepted_synonyms=gt.test_synonyms,
                )
                auto_results["test_checks"].append({
                    "case_id": r.case_id,
                    "system_id": system_id,
                    "is_correct": result.is_correct,
                    "expected": result.expected_test,
                    "detected": result.detected_test,
                    "confidence": result.confidence,
                })

            # Completeness checker (all cases)
            comp = check_completeness(
                case_id=r.case_id,
                system_id=system_id,
                response_text=r.response_text,
            )
            auto_results["completeness_checks"].append({
                "case_id": r.case_id,
                "system_id": system_id,
                "pico_completeness": comp.pico_completeness,
                "bias_count": comp.bias_count,
                "mentions_equator": comp.mentions_equator,
                "has_code_block": comp.has_code_block,
                "word_count": comp.total_word_count,
            })

            # Code validator (biostatistics cases with code)
            if r.code_output and case.biostatistics_ground_truth:
                gt = case.biostatistics_ground_truth
                val = validate_code(
                    case_id=r.case_id,
                    system_id=system_id,
                    code=r.code_output,
                    expected_pattern=gt.expected_code_output_pattern,
                    timeout_seconds=config.code_execution_timeout_seconds,
                )
                auto_results["code_validations"].append({
                    "case_id": r.case_id,
                    "system_id": system_id,
                    "syntax_valid": val.syntax_valid,
                    "executes": val.execution_success,
                    "output_matches": val.ground_truth_match,
                    "error": val.error_text,
                })

    # Save auto-eval results
    out_dir = Path(config.output_dir) / "auto_eval"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "auto_eval_results.json").write_text(
        json.dumps(auto_results, indent=2, default=str)
    )
    logger.info("Auto-eval complete: %d test checks, %d completeness, %d code validations",
                len(auto_results["test_checks"]),
                len(auto_results["completeness_checks"]),
                len(auto_results["code_validations"]))

    return auto_results


async def phase_judge(config: EvalConfig) -> None:
    """Phase 5: Run LLM judge evaluation."""
    cases = load_test_cases()

    chatbot_responses = load_responses("chatbot", config)
    gpt5_responses = load_responses("gpt5", config)

    chatbot_by_case = get_responses_by_case(chatbot_responses)
    gpt5_by_case = get_responses_by_case(gpt5_responses)

    if not chatbot_by_case or not gpt5_by_case:
        logger.error("Missing responses. Run 'collect' phase first.")
        return

    # Create blinded pairs
    pairs = create_blinded_pairs(
        chatbot_by_case, gpt5_by_case, seed=config.random_seed
    )
    logger.info("Created %d blinded pairs", len(pairs))

    # Save blinding map (for later unblinding)
    blinding_map = {
        p.case_id: p.label_to_identity for p in pairs
    }
    out_dir = Path(config.judge_results_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "blinding_map.json").write_text(
        json.dumps(blinding_map, indent=2)
    )

    # Determine which rubric to use per case
    methodology_cases = [c for c in cases if c.agent_target == "methodology"]
    biostats_cases = [c for c in cases if c.agent_target == "biostatistics"]
    # Edge cases get evaluated with methodology rubric by default
    edge_cases = [c for c in cases if c.case_id.startswith("E")]

    all_results = []

    # Evaluate methodology cases
    meth_pairs = [p for p in pairs if any(
        c.case_id == p.case_id for c in methodology_cases + edge_cases
    )]
    if meth_pairs:
        logger.info("Evaluating %d methodology/edge cases...", len(meth_pairs))
        meth_results = await run_full_evaluation(
            meth_pairs, methodology_cases + edge_cases,
            METHODOLOGY_RUBRIC, config
        )
        all_results.extend(meth_results)

    # Evaluate biostatistics cases
    bio_pairs = [p for p in pairs if any(
        c.case_id == p.case_id for c in biostats_cases
    )]
    if bio_pairs:
        logger.info("Evaluating %d biostatistics cases...", len(bio_pairs))
        bio_results = await run_full_evaluation(
            bio_pairs, biostats_cases,
            BIOSTATISTICS_RUBRIC, config
        )
        all_results.extend(bio_results)

    logger.info("Judge evaluation complete: %d total results", len(all_results))


async def run_all(config: EvalConfig) -> None:
    """Run the complete pipeline: collect -> auto-eval -> judge."""
    logger.info("=== Starting full evaluation pipeline ===")

    logger.info("--- Phase 3: Collecting responses ---")
    await phase_collect("both", config)

    logger.info("--- Phase 4: Running automated evaluation ---")
    phase_auto_eval(config)

    logger.info("--- Phase 5: Running LLM judge ---")
    await phase_judge(config)

    logger.info("=== Pipeline complete. Run 'analyze_results.py' for Phase 6. ===")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Evaluation pipeline for medical research chatbot"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # collect subcommand
    collect_parser = subparsers.add_parser("collect", help="Collect responses from systems")
    collect_parser.add_argument(
        "--system", choices=["chatbot", "gpt5", "both"], default="both",
        help="Which system(s) to collect from"
    )

    # auto-eval subcommand
    subparsers.add_parser("auto-eval", help="Run automated evaluation checks")

    # evaluate subcommand
    subparsers.add_parser("evaluate", help="Run LLM judge evaluation")

    # run-all subcommand
    subparsers.add_parser("run-all", help="Run complete pipeline (collect + eval + judge)")

    args = parser.parse_args()
    config = EvalConfig()

    if args.command == "collect":
        asyncio.run(phase_collect(args.system, config))
    elif args.command == "auto-eval":
        phase_auto_eval(config)
    elif args.command == "evaluate":
        asyncio.run(phase_judge(config))
    elif args.command == "run-all":
        asyncio.run(run_all(config))


if __name__ == "__main__":
    main()
