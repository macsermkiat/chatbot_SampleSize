"""Analysis CLI for evaluation results (Phase 6).

Usage:
    python -m evaluation.analyze_results
    python -m evaluation.analyze_results --output-dir evaluation/output/reports
"""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

from evaluation.config import EvalConfig
from evaluation.rubrics.schema import EvaluationResult
from evaluation.rubrics.methodology_rubric import METHODOLOGY_RUBRIC
from evaluation.rubrics.biostatistics_rubric import BIOSTATISTICS_RUBRIC
from evaluation.llm_judge.blinding import BlindedPair
from evaluation.llm_judge.calibration import (
    compute_self_consistency,
    compute_overall_consistency,
)
from evaluation.analysis.descriptive import compute_all_summaries
from evaluation.analysis.comparison import run_full_comparison
from evaluation.analysis.report_generator import (
    ReportConfig,
    generate_full_report,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def load_judge_results(config: EvalConfig) -> list[EvaluationResult]:
    """Load judge results from JSON."""
    filepath = Path(config.judge_results_dir) / "judge_results.json"
    if not filepath.exists():
        logger.error("No judge results found at %s", filepath)
        return []

    data = json.loads(filepath.read_text())
    return [EvaluationResult.model_validate(item) for item in data]


def load_blinding_map(config: EvalConfig) -> dict[str, dict[str, str]]:
    """Load the blinding map to reconstruct pairs."""
    filepath = Path(config.judge_results_dir) / "blinding_map.json"
    if not filepath.exists():
        logger.error("No blinding map found at %s", filepath)
        return {}

    return json.loads(filepath.read_text())


def reconstruct_pairs(blinding_map: dict[str, dict[str, str]]) -> list[BlindedPair]:
    """Reconstruct BlindedPair objects from the blinding map.

    We only need case_id and label_to_identity for analysis.
    The response text fields are not needed at this stage.
    """
    from evaluation.llm_judge.blinding import BlindedResponse

    pairs = []
    for case_id, mapping in blinding_map.items():
        # Create minimal BlindedResponse objects (text not needed for analysis)
        system_a = BlindedResponse(
            case_id=case_id,
            blinded_label="system_a",
            true_identity=mapping.get("system_a", ""),
            text="",
            code="",
            has_execution_result=False,
        )
        system_b = BlindedResponse(
            case_id=case_id,
            blinded_label="system_b",
            true_identity=mapping.get("system_b", ""),
            text="",
            code="",
            has_execution_result=False,
        )
        pairs.append(BlindedPair(
            case_id=case_id,
            system_a=system_a,
            system_b=system_b,
            label_to_identity=mapping,
        ))

    return pairs


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Analyze evaluation results and generate reports"
    )
    parser.add_argument(
        "--output-dir", default=None,
        help="Override report output directory"
    )
    args = parser.parse_args()

    config = EvalConfig()

    # Load results
    results = load_judge_results(config)
    if not results:
        logger.error("No results to analyze. Run evaluation first.")
        return

    blinding_map = load_blinding_map(config)
    if not blinding_map:
        logger.error("No blinding map. Cannot unblind results.")
        return

    pairs = reconstruct_pairs(blinding_map)
    logger.info("Loaded %d results across %d cases", len(results), len(pairs))

    # Compute descriptive statistics
    logger.info("Computing descriptive statistics...")
    summaries = compute_all_summaries(results, pairs)
    chatbot_summary = summaries["chatbot"]
    gpt5_summary = summaries["gpt5"]

    logger.info(
        "Chatbot: n=%d cases, mean_overall=%.2f",
        chatbot_summary.n_cases, chatbot_summary.mean_overall_quality
    )
    logger.info(
        "GPT-5: n=%d cases, mean_overall=%.2f",
        gpt5_summary.n_cases, gpt5_summary.mean_overall_quality
    )

    # Compute paired comparisons
    logger.info("Running statistical comparisons...")
    all_dim_ids = (
        [d.dimension_id for d in METHODOLOGY_RUBRIC.dimensions]
        + [d.dimension_id for d in BIOSTATISTICS_RUBRIC.dimensions]
    )
    comparison = run_full_comparison(results, pairs, all_dim_ids)
    logger.info(
        "Significant dimensions (raw): %d/%d",
        comparison.n_significant_raw, comparison.total_dimensions
    )
    logger.info(
        "Significant dimensions (Bonferroni): %d/%d",
        comparison.n_significant_adjusted, comparison.total_dimensions
    )

    # Judge consistency
    logger.info("Computing judge consistency...")
    consistency_metrics = compute_self_consistency(results)
    overall_consistency = compute_overall_consistency(results)
    logger.info("Overall judge exact agreement: %.2f", overall_consistency)

    # Generate report
    report_dir = args.output_dir or config.reports_dir
    report_config = ReportConfig(output_dir=report_dir)

    logger.info("Generating report...")
    report = generate_full_report(
        chatbot_summary=chatbot_summary,
        gpt5_summary=gpt5_summary,
        comparison=comparison,
        consistency_metrics=consistency_metrics,
        calibration=None,  # Calibration run separately if needed
        config=report_config,
    )

    # Save raw analysis data as JSON
    analysis_dir = Path(config.analysis_dir)
    analysis_dir.mkdir(parents=True, exist_ok=True)

    analysis_data = {
        "chatbot_summary": {
            "n_cases": chatbot_summary.n_cases,
            "mean_overall_quality": chatbot_summary.mean_overall_quality,
            "sd_overall_quality": chatbot_summary.sd_overall_quality,
            "mean_composite": chatbot_summary.mean_composite,
        },
        "gpt5_summary": {
            "n_cases": gpt5_summary.n_cases,
            "mean_overall_quality": gpt5_summary.mean_overall_quality,
            "sd_overall_quality": gpt5_summary.sd_overall_quality,
            "mean_composite": gpt5_summary.mean_composite,
        },
        "comparison": {
            "n_significant_raw": comparison.n_significant_raw,
            "n_significant_adjusted": comparison.n_significant_adjusted,
            "overall_favors": comparison.overall_comparison.favors,
            "overall_p_value": comparison.overall_comparison.p_value,
            "overall_effect_size": comparison.overall_comparison.effect_size_r,
        },
        "judge_consistency": {
            "overall_exact_agreement": overall_consistency,
            "per_dimension": [
                {
                    "dimension_id": m.dimension_id,
                    "exact_rate": m.exact_agreement_rate,
                    "within_one_rate": m.within_one_rate,
                }
                for m in consistency_metrics
            ],
        },
    }

    (analysis_dir / "analysis_summary.json").write_text(
        json.dumps(analysis_data, indent=2, default=str)
    )

    logger.info("Report saved to %s", report_dir)
    logger.info("Analysis data saved to %s", analysis_dir)

    # Print headline results
    oc = comparison.overall_comparison
    print("\n" + "=" * 60)
    print("EVALUATION RESULTS SUMMARY")
    print("=" * 60)
    print(f"Cases evaluated: {chatbot_summary.n_cases}")
    print(f"Chatbot mean overall quality: {chatbot_summary.mean_overall_quality:.2f}")
    print(f"GPT-5 mean overall quality:   {gpt5_summary.mean_overall_quality:.2f}")
    print(f"Overall comparison favors:    {oc.favors}")
    print(f"Overall p-value:              {oc.p_value:.4f}")
    print(f"Overall effect size (r):      {oc.effect_size_r:.3f} ({oc.effect_size_label})")
    print(f"Significant dimensions:       {comparison.n_significant_adjusted}/{comparison.total_dimensions} (Bonferroni)")
    print(f"Judge consistency:            {overall_consistency:.2f}")
    print("=" * 60)


if __name__ == "__main__":
    main()
