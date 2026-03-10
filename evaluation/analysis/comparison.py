"""Statistical comparison between chatbot and GPT-5 evaluation results."""

from __future__ import annotations

import math
from dataclasses import dataclass

from scipy import stats as scipy_stats

from evaluation.analysis.descriptive import build_label_to_identity_map
from evaluation.llm_judge.blinding import BlindedPair
from evaluation.rubrics.schema import EvaluationResult


@dataclass(frozen=True)
class PairedComparison:
    """Result of a paired statistical comparison for one dimension."""

    dimension_id: str
    n_pairs: int
    chatbot_mean: float
    gpt5_mean: float
    mean_difference: float
    wilcoxon_statistic: float
    p_value: float
    p_value_adjusted: float  # Bonferroni-adjusted
    effect_size_r: float  # rank-biserial correlation
    effect_size_label: str  # "small", "medium", "large"
    significant_raw: bool
    significant_adjusted: bool
    favors: str  # "chatbot", "gpt5", or "tie"


@dataclass(frozen=True)
class BinaryComparison:
    """McNemar's test for binary outcomes (e.g., correct/incorrect test selection)."""

    metric_name: str
    chatbot_success_rate: float
    gpt5_success_rate: float
    n: int
    mcnemar_statistic: float
    p_value: float
    significant: bool


@dataclass(frozen=True)
class ComparisonReport:
    """Full comparison report across all dimensions."""

    dimension_comparisons: list[PairedComparison]
    overall_comparison: PairedComparison
    binary_comparisons: list[BinaryComparison]
    n_significant_raw: int
    n_significant_adjusted: int
    total_dimensions: int
    alpha: float
    bonferroni_alpha: float


def _extract_paired_scores(
    results: list[EvaluationResult],
    pairs: list[BlindedPair],
    dimension_id: str,
) -> tuple[list[float], list[float]]:
    """Extract paired score vectors for chatbot and gpt5.

    Averages across judge runs for each (case, system) combination.
    Returns (chatbot_scores, gpt5_scores) aligned by case.
    """
    identity_map = build_label_to_identity_map(pairs)

    # Group scores by (case_id, true_identity, dimension_id)
    grouped: dict[tuple[str, str], list[int]] = {}
    for r in results:
        case_mapping = identity_map.get(r.case_id, {})
        true_id = case_mapping.get(r.system_id, "")
        if not true_id:
            continue
        for ds in r.dimension_scores:
            if ds.dimension_id == dimension_id:
                key = (r.case_id, true_id)
                grouped.setdefault(key, []).append(ds.score)

    # Average across judge runs and build paired vectors
    chatbot_scores = []
    gpt5_scores = []

    case_ids = {pair.case_id for pair in pairs}
    for case_id in sorted(case_ids):
        chatbot_key = (case_id, "chatbot")
        gpt5_key = (case_id, "gpt5")
        if chatbot_key in grouped and gpt5_key in grouped:
            chatbot_avg = sum(grouped[chatbot_key]) / len(grouped[chatbot_key])
            gpt5_avg = sum(grouped[gpt5_key]) / len(grouped[gpt5_key])
            chatbot_scores.append(chatbot_avg)
            gpt5_scores.append(gpt5_avg)

    return chatbot_scores, gpt5_scores


def _extract_paired_overall(
    results: list[EvaluationResult],
    pairs: list[BlindedPair],
) -> tuple[list[float], list[float]]:
    """Extract paired overall quality scores."""
    identity_map = build_label_to_identity_map(pairs)

    grouped: dict[tuple[str, str], list[int]] = {}
    for r in results:
        case_mapping = identity_map.get(r.case_id, {})
        true_id = case_mapping.get(r.system_id, "")
        if true_id:
            key = (r.case_id, true_id)
            grouped.setdefault(key, []).append(r.overall_quality)

    chatbot_scores = []
    gpt5_scores = []
    for case_id in sorted({p.case_id for p in pairs}):
        ck = (case_id, "chatbot")
        gk = (case_id, "gpt5")
        if ck in grouped and gk in grouped:
            chatbot_scores.append(sum(grouped[ck]) / len(grouped[ck]))
            gpt5_scores.append(sum(grouped[gk]) / len(grouped[gk]))

    return chatbot_scores, gpt5_scores


def wilcoxon_comparison(
    chatbot_scores: list[float],
    gpt5_scores: list[float],
    dimension_id: str,
    n_comparisons: int = 16,
    alpha: float = 0.05,
) -> PairedComparison:
    """Run Wilcoxon signed-rank test on paired scores.

    Args:
        chatbot_scores: Scores for chatbot (aligned by case).
        gpt5_scores: Scores for GPT-5 (aligned by case).
        dimension_id: Which dimension is being compared.
        n_comparisons: Total comparisons for Bonferroni correction.
        alpha: Significance level before correction.
    """
    n = len(chatbot_scores)
    if n < 5:
        return PairedComparison(
            dimension_id=dimension_id,
            n_pairs=n,
            chatbot_mean=_safe_mean(chatbot_scores),
            gpt5_mean=_safe_mean(gpt5_scores),
            mean_difference=0.0,
            wilcoxon_statistic=0.0,
            p_value=1.0,
            p_value_adjusted=1.0,
            effect_size_r=0.0,
            effect_size_label="insufficient data",
            significant_raw=False,
            significant_adjusted=False,
            favors="tie",
        )

    differences = [c - g for c, g in zip(chatbot_scores, gpt5_scores)]
    mean_diff = _safe_mean(differences)

    # Remove zero differences for Wilcoxon
    nonzero_diffs = [d for d in differences if d != 0.0]
    if len(nonzero_diffs) < 2:
        return PairedComparison(
            dimension_id=dimension_id,
            n_pairs=n,
            chatbot_mean=_safe_mean(chatbot_scores),
            gpt5_mean=_safe_mean(gpt5_scores),
            mean_difference=mean_diff,
            wilcoxon_statistic=0.0,
            p_value=1.0,
            p_value_adjusted=1.0,
            effect_size_r=0.0,
            effect_size_label="no difference",
            significant_raw=False,
            significant_adjusted=False,
            favors="tie",
        )

    stat, p_value = scipy_stats.wilcoxon(
        chatbot_scores, gpt5_scores, alternative="two-sided"
    )

    # Effect size: rank-biserial correlation r = Z / sqrt(N)
    # Approximate Z from p-value
    z_score = scipy_stats.norm.ppf(1 - p_value / 2) if p_value < 1.0 else 0.0
    effect_r = z_score / math.sqrt(n) if n > 0 else 0.0

    # Classify effect size
    abs_r = abs(effect_r)
    if abs_r < 0.1:
        effect_label = "negligible"
    elif abs_r < 0.3:
        effect_label = "small"
    elif abs_r < 0.5:
        effect_label = "medium"
    else:
        effect_label = "large"

    adjusted_p = min(1.0, p_value * n_comparisons)
    bonferroni_alpha = alpha / n_comparisons

    if mean_diff > 0:
        favors = "chatbot"
    elif mean_diff < 0:
        favors = "gpt5"
    else:
        favors = "tie"

    return PairedComparison(
        dimension_id=dimension_id,
        n_pairs=n,
        chatbot_mean=_safe_mean(chatbot_scores),
        gpt5_mean=_safe_mean(gpt5_scores),
        mean_difference=mean_diff,
        wilcoxon_statistic=float(stat),
        p_value=p_value,
        p_value_adjusted=adjusted_p,
        effect_size_r=effect_r,
        effect_size_label=effect_label,
        significant_raw=p_value < alpha,
        significant_adjusted=adjusted_p < alpha,
        favors=favors,
    )


def mcnemar_comparison(
    chatbot_correct: list[bool],
    gpt5_correct: list[bool],
    metric_name: str,
    alpha: float = 0.05,
) -> BinaryComparison:
    """McNemar's test for paired binary outcomes.

    Args:
        chatbot_correct: Boolean correctness for chatbot per case.
        gpt5_correct: Boolean correctness for GPT-5 per case.
        metric_name: Name of the metric being compared.
    """
    n = len(chatbot_correct)
    if n == 0:
        return BinaryComparison(
            metric_name=metric_name,
            chatbot_success_rate=0.0,
            gpt5_success_rate=0.0,
            n=0,
            mcnemar_statistic=0.0,
            p_value=1.0,
            significant=False,
        )

    # Contingency: b = chatbot correct & gpt5 wrong, c = chatbot wrong & gpt5 correct
    b = sum(1 for cb, gp in zip(chatbot_correct, gpt5_correct) if cb and not gp)
    c = sum(1 for cb, gp in zip(chatbot_correct, gpt5_correct) if not cb and gp)

    if b + c == 0:
        stat, p_val = 0.0, 1.0
    elif b + c < 25:
        # Use exact binomial test for small samples
        p_val = scipy_stats.binom_test(b, b + c, 0.5) if (b + c) > 0 else 1.0
        stat = float(b - c)
    else:
        # McNemar's chi-square with continuity correction
        stat = (abs(b - c) - 1) ** 2 / (b + c) if (b + c) > 0 else 0.0
        p_val = 1 - scipy_stats.chi2.cdf(stat, df=1)

    return BinaryComparison(
        metric_name=metric_name,
        chatbot_success_rate=sum(chatbot_correct) / n,
        gpt5_success_rate=sum(gpt5_correct) / n,
        n=n,
        mcnemar_statistic=float(stat),
        p_value=p_val,
        significant=p_val < alpha,
    )


def run_full_comparison(
    results: list[EvaluationResult],
    pairs: list[BlindedPair],
    dimension_ids: list[str],
    alpha: float = 0.05,
) -> ComparisonReport:
    """Run complete paired comparison across all dimensions.

    Args:
        results: All evaluation results from judge.
        pairs: Blinded pairs for identity mapping.
        dimension_ids: List of dimension IDs to compare.
        alpha: Base significance level.
    """
    n_comparisons = len(dimension_ids) + 1  # +1 for overall quality

    dim_comparisons = []
    for dim_id in dimension_ids:
        chatbot_scores, gpt5_scores = _extract_paired_scores(
            results, pairs, dim_id
        )
        comparison = wilcoxon_comparison(
            chatbot_scores, gpt5_scores, dim_id, n_comparisons, alpha
        )
        dim_comparisons.append(comparison)

    # Overall quality comparison
    chatbot_overall, gpt5_overall = _extract_paired_overall(results, pairs)
    overall_comp = wilcoxon_comparison(
        chatbot_overall, gpt5_overall, "overall", n_comparisons, alpha
    )

    n_sig_raw = sum(1 for c in dim_comparisons if c.significant_raw)
    n_sig_adj = sum(1 for c in dim_comparisons if c.significant_adjusted)

    return ComparisonReport(
        dimension_comparisons=dim_comparisons,
        overall_comparison=overall_comp,
        binary_comparisons=[],  # Populated separately with auto-eval results
        n_significant_raw=n_sig_raw,
        n_significant_adjusted=n_sig_adj,
        total_dimensions=len(dimension_ids),
        alpha=alpha,
        bonferroni_alpha=alpha / n_comparisons,
    )


def _safe_mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0
