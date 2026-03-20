"""Sample size validation — compare ProtoCol outputs against published benchmarks.

Loads benchmark scenarios with known expected sample sizes and scores
concordance as exact match, within 5%, or within 10%.
"""

from __future__ import annotations

import json
import statistics
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


_BENCHMARKS_PATH = Path(__file__).parent.parent / "test_cases" / "validation_benchmarks.json"


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------


class Benchmark(BaseModel):
    """A single validation benchmark with known expected sample size."""

    id: str
    scenario: str
    description: str = ""
    parameters: dict[str, Any] = Field(default_factory=dict)
    expected: dict[str, Any] = Field(default_factory=dict)
    tolerance_5pct: tuple[int, int]
    tolerance_10pct: tuple[int, int]


class BenchmarkSuite(BaseModel):
    """Collection of validation benchmarks."""

    version: str = "1.0.0"
    description: str = ""
    benchmarks: list[Benchmark]


def load_benchmarks(path: Path | None = None) -> BenchmarkSuite:
    """Load benchmarks from JSON file."""
    p = path or _BENCHMARKS_PATH
    data = json.loads(p.read_text())
    return BenchmarkSuite(**data)


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ScoreResult:
    """Result of scoring a single benchmark."""

    benchmark_id: str
    actual: int
    expected: int
    exact_match: bool
    within_5pct: bool
    within_10pct: bool
    deviation_pct: float


def score_result(
    actual: int,
    expected: int,
    tolerance_5pct: tuple[int, int],
    tolerance_10pct: tuple[int, int],
) -> ScoreResult:
    """Score a single result against a benchmark.

    Args:
        actual: The sample size computed by ProtoCol.
        expected: The known correct sample size.
        tolerance_5pct: Acceptable range for 5% concordance (min, max).
        tolerance_10pct: Acceptable range for 10% concordance (min, max).
    """
    if expected == 0:
        return ScoreResult(
            benchmark_id="",
            actual=actual,
            expected=expected,
            exact_match=actual == 0,
            within_5pct=False,
            within_10pct=False,
            deviation_pct=100.0 if actual != 0 else 0.0,
        )

    deviation_pct = abs(actual - expected) / expected * 100

    return ScoreResult(
        benchmark_id="",
        actual=actual,
        expected=expected,
        exact_match=actual == expected,
        within_5pct=tolerance_5pct[0] <= actual <= tolerance_5pct[1],
        within_10pct=tolerance_10pct[0] <= actual <= tolerance_10pct[1],
        deviation_pct=round(deviation_pct, 2),
    )


# ---------------------------------------------------------------------------
# Concordance summary
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ConcordanceSummary:
    """Aggregate concordance statistics across all benchmarks."""

    total: int
    exact_match_count: int
    within_5pct_count: int
    within_10pct_count: int
    exact_match_rate: float
    within_5pct_rate: float
    within_10pct_rate: float
    mean_deviation_pct: float
    median_deviation_pct: float


def compute_concordance(scores: list[ScoreResult]) -> ConcordanceSummary:
    """Compute concordance summary from a list of score results."""
    if not scores:
        return ConcordanceSummary(
            total=0,
            exact_match_count=0,
            within_5pct_count=0,
            within_10pct_count=0,
            exact_match_rate=0.0,
            within_5pct_rate=0.0,
            within_10pct_rate=0.0,
            mean_deviation_pct=0.0,
            median_deviation_pct=0.0,
        )

    total = len(scores)
    exact_count = sum(1 for s in scores if s.exact_match)
    within_5_count = sum(1 for s in scores if s.within_5pct)
    within_10_count = sum(1 for s in scores if s.within_10pct)
    deviations = [s.deviation_pct for s in scores]

    return ConcordanceSummary(
        total=total,
        exact_match_count=exact_count,
        within_5pct_count=within_5_count,
        within_10pct_count=within_10_count,
        exact_match_rate=round(exact_count / total * 100, 2),
        within_5pct_rate=round(within_5_count / total * 100, 2),
        within_10pct_rate=round(within_10_count / total * 100, 2),
        mean_deviation_pct=round(statistics.mean(deviations), 2),
        median_deviation_pct=round(statistics.median(deviations), 2),
    )


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------


def generate_validation_report(
    scores: list[ScoreResult],
    summary: ConcordanceSummary,
) -> str:
    """Generate a publishable Markdown validation report.

    Returns the full report as a string.
    """
    lines: list[str] = []

    lines.append("# Sample Size Calculation Validation Report")
    lines.append("")
    lines.append("## Concordance Summary")
    lines.append("")
    lines.append("| Metric | Value |")
    lines.append("|---|---|")
    lines.append(f"| Total benchmarks | {summary.total} |")
    lines.append(f"| Exact match | {summary.exact_match_count}/{summary.total} ({summary.exact_match_rate:.1f}%) |")
    lines.append(f"| Within 5% | {summary.within_5pct_count}/{summary.total} ({summary.within_5pct_rate:.1f}%) |")
    lines.append(f"| Within 10% | {summary.within_10pct_count}/{summary.total} ({summary.within_10pct_rate:.1f}%) |")
    lines.append(f"| Mean deviation | {summary.mean_deviation_pct:.2f}% |")
    lines.append(f"| Median deviation | {summary.median_deviation_pct:.2f}% |")
    lines.append("")

    lines.append("## Detailed Results")
    lines.append("")
    lines.append("| Benchmark | Expected | Actual | Deviation | Exact | 5% | 10% |")
    lines.append("|---|---|---|---|---|---|---|")

    for s in scores:
        exact_mark = "Y" if s.exact_match else ""
        within5_mark = "Y" if s.within_5pct else ""
        within10_mark = "Y" if s.within_10pct else ""
        lines.append(
            f"| {s.benchmark_id} | {s.expected} | {s.actual} | "
            f"{s.deviation_pct:.1f}% | {exact_mark} | {within5_mark} | {within10_mark} |"
        )

    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append(
        "*Validation performed against published formulas from "
        "Chow et al. (2018), Machin et al. (2018), Julious (2023), "
        "and statsmodels/scipy reference implementations.*"
    )

    return "\n".join(lines)
