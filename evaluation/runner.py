"""Main orchestrator CLI for the evaluation pipeline (Phases 3-6).

Usage:
    python -m evaluation.runner collect --system chatbot
    python -m evaluation.runner collect --system gpt5
    python -m evaluation.runner collect --system both
    python -m evaluation.runner evaluate
    python -m evaluation.runner analyze
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
from evaluation.llm_judge.calibration import compute_self_consistency
from evaluation.analysis.descriptive import compute_all_summaries
from evaluation.analysis.comparison import run_full_comparison
from evaluation.analysis.report_generator import generate_full_report, ReportConfig

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

    all_results: list = []

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

    # Evaluate biostatistics cases (pass existing methodology results
    # so incremental saves don't overwrite them)
    bio_pairs = [p for p in pairs if any(
        c.case_id == p.case_id for c in biostats_cases
    )]
    if bio_pairs:
        logger.info("Evaluating %d biostatistics cases...", len(bio_pairs))
        bio_results = await run_full_evaluation(
            bio_pairs, biostats_cases,
            BIOSTATISTICS_RUBRIC, config,
            existing_results=all_results,
        )
        all_results.extend(bio_results)

    # Final save of all combined results
    from evaluation.llm_judge.judge_runner import _save_results
    _save_results(all_results, config)
    logger.info("Judge evaluation complete: %d total results saved", len(all_results))


def phase_analyze(
    config: EvalConfig,
    exclude_cases: set[str] | None = None,
    report_suffix: str = "",
) -> str:
    """Phase 6: Generate statistical comparison and final report.

    Args:
        config: Evaluation configuration.
        exclude_cases: Case IDs to exclude from analysis (e.g., routing failures).
        report_suffix: Suffix for output filenames (e.g., "_filtered").
    """
    exclude = exclude_cases or set()

    # Load judge results
    judge_path = Path(config.judge_results_dir) / "judge_results.json"
    if not judge_path.exists():
        logger.error("No judge results found. Run 'evaluate' first.")
        return ""
    raw_results = json.loads(judge_path.read_text())

    from evaluation.rubrics.schema import EvaluationResult, DimensionScore
    results = [EvaluationResult.model_validate(r) for r in raw_results]
    logger.info("Loaded %d judge results", len(results))

    # Deduplicate results: keep latest per (case_id, system_id, judge_run, rubric_id)
    seen: dict[tuple, EvaluationResult] = {}
    for r in results:
        key = (r.case_id, r.system_id, r.judge_run, r.rubric_id)
        seen[key] = r  # last one wins
    results = list(seen.values())
    logger.info("After dedup: %d results", len(results))

    # Apply exclusions
    if exclude:
        before = len(results)
        results = [r for r in results if r.case_id not in exclude]
        logger.info(
            "Excluded %d cases (%s): %d -> %d results",
            len(exclude), sorted(exclude), before, len(results),
        )

    # Recreate blinded pairs for identity mapping
    chatbot_responses = load_responses("chatbot", config)
    gpt5_responses = load_responses("gpt5", config)
    chatbot_by_case = get_responses_by_case(chatbot_responses)
    gpt5_by_case = get_responses_by_case(gpt5_responses)
    pairs = create_blinded_pairs(chatbot_by_case, gpt5_by_case, seed=config.random_seed)

    # Filter pairs to match excluded cases
    if exclude:
        pairs = [p for p in pairs if p.case_id not in exclude]

    # Compute descriptive summaries
    summaries = compute_all_summaries(results, pairs)
    chatbot_summary = summaries["chatbot"]
    gpt5_summary = summaries["gpt5"]

    logger.info(
        "Chatbot: %d cases, mean overall=%.2f, composite=%.2f",
        chatbot_summary.n_cases, chatbot_summary.mean_overall_quality,
        chatbot_summary.mean_composite,
    )
    logger.info(
        "GPT-5: %d cases, mean overall=%.2f, composite=%.2f",
        gpt5_summary.n_cases, gpt5_summary.mean_overall_quality,
        gpt5_summary.mean_composite,
    )

    # Collect all dimension IDs from results
    all_dim_ids = sorted({
        ds.dimension_id for r in results for ds in r.dimension_scores
    })
    logger.info("Dimensions found: %s", all_dim_ids)

    # Run statistical comparison
    comparison = run_full_comparison(results, pairs, all_dim_ids)

    # Self-consistency metrics
    consistency = compute_self_consistency(results)

    # Use suffixed output directory for filtered reports
    report_dir = config.reports_dir
    if report_suffix:
        report_dir = str(Path(config.reports_dir) / f"filtered{report_suffix}")

    # Generate report
    report_config = ReportConfig(
        output_dir=report_dir,
        excluded_cases=tuple(sorted(exclude)) if exclude else (),
        exclusion_reasons=(
            "routing/deferral failures and asymmetric follow-up methodology confounds"
            if exclude else ""
        ),
    )
    report = generate_full_report(
        chatbot_summary=chatbot_summary,
        gpt5_summary=gpt5_summary,
        comparison=comparison,
        consistency_metrics=consistency,
        calibration=None,
        config=report_config,
    )

    logger.info("Report saved to %s/evaluation_report.md", report_dir)

    # Print summary to stdout
    oc = comparison.overall_comparison
    print("\n" + "=" * 70)
    title = "EVALUATION RESULTS SUMMARY"
    if exclude:
        title += f" (excluded {len(exclude)} cases)"
    print(title)
    print("=" * 70)
    if exclude:
        print(f"Excluded cases: {sorted(exclude)}")
    print(f"\nCases evaluated: {chatbot_summary.n_cases}")
    print(f"\n{'Metric':<30} {'Chatbot':>10} {'GPT-5':>10}")
    print("-" * 50)
    print(f"{'Mean Overall Quality':<30} {chatbot_summary.mean_overall_quality:>10.2f} {gpt5_summary.mean_overall_quality:>10.2f}")
    print(f"{'Mean Composite Score':<30} {chatbot_summary.mean_composite:>10.2f} {gpt5_summary.mean_composite:>10.2f}")

    print(f"\nOverall: favors {oc.favors} (p={oc.p_value:.4f}, r={oc.effect_size_r:.2f} [{oc.effect_size_label}])")
    print(f"Significant dimensions (Bonferroni): {comparison.n_significant_adjusted}/{comparison.total_dimensions}")

    print(f"\n{'Dimension':<12} {'Chatbot':>10} {'GPT-5':>10} {'Diff':>8} {'p-adj':>10} {'Effect':>10} {'Favors':>8}")
    print("-" * 70)
    for c in comparison.dimension_comparisons:
        sig = "***" if c.significant_adjusted else ("*" if c.significant_raw else "")
        print(f"{c.dimension_id:<12} {c.chatbot_mean:>10.2f} {c.gpt5_mean:>10.2f} {c.mean_difference:>+8.2f} {c.p_value_adjusted:>10.4f} {c.effect_size_label:>10} {c.favors:>8} {sig}")

    print(f"\n{'overall':<12} {oc.chatbot_mean:>10.2f} {oc.gpt5_mean:>10.2f} {oc.mean_difference:>+8.2f} {oc.p_value_adjusted:>10.4f} {oc.effect_size_label:>10} {oc.favors:>8}")
    print("=" * 70)

    return report


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

    # analyze subcommand
    analyze_parser = subparsers.add_parser("analyze", help="Generate statistical comparison and report")
    analyze_parser.add_argument(
        "--exclude-cases", nargs="*", default=[],
        help="Case IDs to exclude from analysis (e.g., B10 B11 E02)",
    )

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
    elif args.command == "analyze":
        excluded = set(args.exclude_cases) if args.exclude_cases else set()
        suffix = "_excluded" if excluded else ""
        phase_analyze(config, exclude_cases=excluded, report_suffix=suffix)
    elif args.command == "run-all":
        asyncio.run(run_all(config))


if __name__ == "__main__":
    main()
