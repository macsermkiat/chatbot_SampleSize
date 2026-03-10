"""Gold standard calibration and self-consistency measurement for LLM judge."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from collections import Counter

from evaluation.rubrics.schema import EvaluationResult

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ConsistencyMetrics:
    """Self-consistency metrics across multiple judge runs."""

    dimension_id: str
    total_comparisons: int
    exact_agreement: int
    within_one_agreement: int
    exact_agreement_rate: float
    within_one_rate: float


@dataclass(frozen=True)
class CalibrationResult:
    """Result of calibrating judge against gold standard responses."""

    gold_case_id: str
    dimension_id: str
    expected_score: int
    judge_score: int
    is_exact_match: bool
    is_within_one: bool


@dataclass(frozen=True)
class CalibrationReport:
    """Aggregated calibration report."""

    total_cases: int
    total_dimensions: int
    exact_match_rate: float
    within_one_rate: float
    per_dimension: dict[str, float]  # dimension_id -> exact match rate
    passed: bool  # True if within_one_rate >= threshold


# Gold standard test pairs with predetermined scores.
# These are used to validate the judge before running full evaluation.
# Format: (case_id, dimension_id, expected_score, response_quality_description)
GOLD_STANDARDS: list[dict] = [
    {
        "gold_id": "gold_01",
        "description": "Perfect methodology response: complete PICOTS, TTE reasoning",
        "dimension_id": "M1",
        "expected_score": 5,
        "response_text": (
            "## PICOTS Framework\n\n"
            "**Population (P):** Adults aged 18-75 with newly diagnosed "
            "type 2 diabetes (HbA1c 7.0-10.0%), no prior insulin use, "
            "BMI 25-40 kg/m2.\n\n"
            "**Intervention (I):** SGLT2 inhibitor (empagliflozin 10mg daily) "
            "initiated within 3 months of diagnosis.\n\n"
            "**Comparator (C):** Metformin monotherapy (titrated to 2000mg/day), "
            "representing current standard of care per ADA 2024 guidelines.\n\n"
            "**Outcome (O):** Primary: composite of major adverse cardiovascular "
            "events (MACE - cardiovascular death, non-fatal MI, non-fatal stroke) "
            "at 36 months. Secondary: HbA1c reduction, eGFR slope, "
            "hospitalization for heart failure.\n\n"
            "**Timeframe (T):** 36-month follow-up with interim analyses at "
            "12 and 24 months.\n\n"
            "**Setting (S):** Multicenter trial across tertiary care diabetes "
            "clinics and community health centers in Southeast Asia, ensuring "
            "generalizability to the regional population."
        ),
    },
    {
        "gold_id": "gold_02",
        "description": "Poor methodology: no PICO, vague advice",
        "dimension_id": "M1",
        "expected_score": 1,
        "response_text": (
            "You should probably do a study on diabetes treatment. "
            "Compare some drugs and see which works better. "
            "Maybe follow up for a while and check the results."
        ),
    },
    {
        "gold_id": "gold_03",
        "description": "Good biostatistics: correct test with basic justification",
        "dimension_id": "B1",
        "expected_score": 4,
        "response_text": (
            "For comparing HbA1c reduction between two independent treatment "
            "groups (empagliflozin vs metformin), the appropriate primary "
            "analysis is an **independent two-sample t-test** (or Welch's "
            "t-test if variance equality is questionable).\n\n"
            "**Justification:**\n"
            "- The outcome (HbA1c change from baseline) is continuous\n"
            "- Two independent groups (parallel design)\n"
            "- With n>30 per group, CLT supports approximate normality\n\n"
            "**Alternative if assumptions fail:** Mann-Whitney U test as "
            "non-parametric fallback.\n\n"
            "**Note:** Consider ANCOVA adjusting for baseline HbA1c for "
            "improved precision."
        ),
    },
    {
        "gold_id": "gold_04",
        "description": "Adequate sample size calculation with missing adjustments",
        "dimension_id": "B2",
        "expected_score": 3,
        "response_text": (
            "## Sample Size Calculation\n\n"
            "Using a two-sample t-test framework:\n"
            "- Effect size: 0.5% HbA1c difference (clinically meaningful)\n"
            "- SD: 1.2% (from literature)\n"
            "- Alpha: 0.05 (two-sided)\n"
            "- Power: 80%\n\n"
            "n = 2 * ((1.96 + 0.84)^2 * 1.2^2) / 0.5^2 = ~91 per group\n\n"
            "Total: 182 participants."
        ),
    },
    {
        "gold_id": "gold_05",
        "description": "Excellent explanation quality for novice audience",
        "dimension_id": "M7",
        "expected_score": 5,
        "response_text": (
            "Let me explain this step by step, as if we were planning a "
            "cooking experiment.\n\n"
            "**What is a Randomized Controlled Trial (RCT)?**\n"
            "Think of it like a taste test: you randomly assign people to "
            "try either Recipe A (new drug) or Recipe B (standard drug), "
            "without them knowing which one they got. This way, any "
            "difference in how they feel is likely due to the recipe, not "
            "personal preference.\n\n"
            "**Why randomize?**\n"
            "If we let people choose their own treatment, those who chose "
            "the new drug might be systematically different (younger, "
            "healthier, more motivated). Randomization ensures the groups "
            "are comparable.\n\n"
            "**What is 'blinding'?**\n"
            "Neither the patient nor the doctor knows which treatment was "
            "given. This prevents the placebo effect and unconscious bias "
            "in how outcomes are measured.\n\n"
            "**Your key takeaway:** An RCT is the strongest evidence for "
            "proving that a treatment actually works, rather than just being "
            "associated with better outcomes."
        ),
    },
]


def compute_self_consistency(
    results: list[EvaluationResult],
) -> list[ConsistencyMetrics]:
    """Measure judge self-consistency across repeated runs.

    Groups results by (case_id, system_id, dimension_id) and checks
    whether scores agree across the 3 judge runs.
    """
    # Group scores by (case, system, dimension)
    grouped: dict[tuple[str, str, str], list[int]] = {}
    for result in results:
        for ds in result.dimension_scores:
            key = (result.case_id, result.system_id, ds.dimension_id)
            grouped.setdefault(key, []).append(ds.score)

    # Compute per-dimension consistency
    dim_exact: dict[str, list[bool]] = {}
    dim_within_one: dict[str, list[bool]] = {}

    for (_, _, dim_id), scores in grouped.items():
        if len(scores) < 2:
            continue

        # Compare all pairs of runs
        for i in range(len(scores)):
            for j in range(i + 1, len(scores)):
                dim_exact.setdefault(dim_id, []).append(scores[i] == scores[j])
                dim_within_one.setdefault(dim_id, []).append(
                    abs(scores[i] - scores[j]) <= 1
                )

    metrics = []
    for dim_id in sorted(dim_exact.keys()):
        exact = dim_exact[dim_id]
        within = dim_within_one[dim_id]
        metrics.append(
            ConsistencyMetrics(
                dimension_id=dim_id,
                total_comparisons=len(exact),
                exact_agreement=sum(exact),
                within_one_agreement=sum(within),
                exact_agreement_rate=sum(exact) / len(exact) if exact else 0.0,
                within_one_rate=sum(within) / len(within) if within else 0.0,
            )
        )

    return metrics


def compute_overall_consistency(
    results: list[EvaluationResult],
) -> float:
    """Compute single overall consistency score (% exact agreement)."""
    metrics = compute_self_consistency(results)
    if not metrics:
        return 0.0
    total_exact = sum(m.exact_agreement for m in metrics)
    total_comps = sum(m.total_comparisons for m in metrics)
    return total_exact / total_comps if total_comps > 0 else 0.0


def evaluate_gold_standards(
    calibration_results: list[CalibrationResult],
    threshold: float = 0.80,
) -> CalibrationReport:
    """Evaluate judge performance against gold standard responses.

    Args:
        calibration_results: Results from running judge on gold standards.
        threshold: Minimum within-one agreement rate to pass calibration.

    Returns:
        CalibrationReport with aggregated metrics.
    """
    if not calibration_results:
        return CalibrationReport(
            total_cases=0,
            total_dimensions=0,
            exact_match_rate=0.0,
            within_one_rate=0.0,
            per_dimension={},
            passed=False,
        )

    total = len(calibration_results)
    exact_matches = sum(1 for r in calibration_results if r.is_exact_match)
    within_one_matches = sum(1 for r in calibration_results if r.is_within_one)

    # Per-dimension breakdown
    dim_results: dict[str, list[bool]] = {}
    for r in calibration_results:
        dim_results.setdefault(r.dimension_id, []).append(r.is_exact_match)

    per_dim = {
        dim_id: sum(matches) / len(matches) if matches else 0.0
        for dim_id, matches in dim_results.items()
    }

    within_one_rate = within_one_matches / total if total > 0 else 0.0

    unique_cases = len({r.gold_case_id for r in calibration_results})
    unique_dims = len(dim_results)

    return CalibrationReport(
        total_cases=unique_cases,
        total_dimensions=unique_dims,
        exact_match_rate=exact_matches / total if total > 0 else 0.0,
        within_one_rate=within_one_rate,
        per_dimension=per_dim,
        passed=within_one_rate >= threshold,
    )


def check_score_distribution(
    results: list[EvaluationResult],
) -> dict[str, dict[int, int]]:
    """Check for score distribution anomalies (e.g., all 3s).

    Returns mapping of dimension_id -> {score: count}.
    """
    dist: dict[str, dict[int, int]] = {}
    for result in results:
        for ds in result.dimension_scores:
            if ds.dimension_id not in dist:
                dist[ds.dimension_id] = Counter()
            dist[ds.dimension_id][ds.score] += 1

    return {dim_id: dict(counts) for dim_id, counts in dist.items()}
