"""Descriptive statistics for evaluation results."""

from __future__ import annotations

import statistics
from dataclasses import dataclass

from evaluation.llm_judge.blinding import BlindedPair
from evaluation.rubrics.schema import EvaluationResult


@dataclass(frozen=True)
class DimensionSummary:
    """Descriptive statistics for a single dimension."""

    dimension_id: str
    system_id: str  # true identity: "chatbot" or "gpt5"
    n: int
    mean: float
    median: float
    sd: float
    min_score: int
    max_score: int
    q25: float
    q75: float
    score_distribution: dict[int, int]  # score -> count


@dataclass(frozen=True)
class SystemSummary:
    """Overall summary for one system across all dimensions."""

    system_id: str
    n_cases: int
    mean_overall_quality: float
    sd_overall_quality: float
    mean_composite: float
    dimension_summaries: list[DimensionSummary]


def compute_dimension_summary(
    scores: list[int],
    dimension_id: str,
    system_id: str,
) -> DimensionSummary:
    """Compute descriptive stats for a list of scores."""
    if not scores:
        return DimensionSummary(
            dimension_id=dimension_id,
            system_id=system_id,
            n=0,
            mean=0.0,
            median=0.0,
            sd=0.0,
            min_score=0,
            max_score=0,
            q25=0.0,
            q75=0.0,
            score_distribution={},
        )

    sorted_scores = sorted(scores)
    n = len(sorted_scores)
    q25_idx = max(0, int(n * 0.25) - 1)
    q75_idx = min(n - 1, int(n * 0.75))

    dist: dict[int, int] = {}
    for s in scores:
        dist[s] = dist.get(s, 0) + 1

    return DimensionSummary(
        dimension_id=dimension_id,
        system_id=system_id,
        n=n,
        mean=statistics.mean(scores),
        median=statistics.median(scores),
        sd=statistics.stdev(scores) if n > 1 else 0.0,
        min_score=min(scores),
        max_score=max(scores),
        q25=float(sorted_scores[q25_idx]),
        q75=float(sorted_scores[q75_idx]),
        score_distribution=dist,
    )


def compute_system_summary(
    results: list[EvaluationResult],
    true_identity: str,
    label_to_identity: dict[str, dict[str, str]],
) -> SystemSummary:
    """Compute summary statistics for one system (after unblinding).

    Args:
        results: All evaluation results.
        true_identity: "chatbot" or "gpt5".
        label_to_identity: case_id -> {blinded_label: true_identity}.
    """
    # Filter results for this system
    system_results = []
    for r in results:
        case_mapping = label_to_identity.get(r.case_id, {})
        if case_mapping.get(r.system_id) == true_identity:
            system_results.append(r)

    if not system_results:
        return SystemSummary(
            system_id=true_identity,
            n_cases=0,
            mean_overall_quality=0.0,
            sd_overall_quality=0.0,
            mean_composite=0.0,
            dimension_summaries=[],
        )

    # Overall quality scores
    overall_scores = [r.overall_quality for r in system_results]
    composite_scores = [r.composite_score for r in system_results]

    # Per-dimension scores
    dim_scores: dict[str, list[int]] = {}
    for r in system_results:
        for ds in r.dimension_scores:
            dim_scores.setdefault(ds.dimension_id, []).append(ds.score)

    dim_summaries = [
        compute_dimension_summary(scores, dim_id, true_identity)
        for dim_id, scores in sorted(dim_scores.items())
    ]

    case_ids = {r.case_id for r in system_results}

    return SystemSummary(
        system_id=true_identity,
        n_cases=len(case_ids),
        mean_overall_quality=statistics.mean(overall_scores),
        sd_overall_quality=(
            statistics.stdev(overall_scores) if len(overall_scores) > 1 else 0.0
        ),
        mean_composite=statistics.mean(composite_scores),
        dimension_summaries=dim_summaries,
    )


def build_label_to_identity_map(
    pairs: list[BlindedPair],
) -> dict[str, dict[str, str]]:
    """Build case_id -> {blinded_label: true_identity} mapping."""
    return {pair.case_id: dict(pair.label_to_identity) for pair in pairs}


def compute_all_summaries(
    results: list[EvaluationResult],
    pairs: list[BlindedPair],
) -> dict[str, SystemSummary]:
    """Compute summaries for both systems.

    Returns dict with keys "chatbot" and "gpt5".
    """
    identity_map = build_label_to_identity_map(pairs)
    return {
        system: compute_system_summary(results, system, identity_map)
        for system in ("chatbot", "gpt5")
    }
