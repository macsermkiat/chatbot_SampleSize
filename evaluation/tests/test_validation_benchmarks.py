"""Tests for sample size validation benchmarks and validator (Phase 4: TDD RED).

Tests the benchmark schema, scoring logic, and report generation.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest


BENCHMARKS_PATH = Path(__file__).parent.parent / "test_cases" / "validation_benchmarks.json"


# ---------------------------------------------------------------------------
# 1. Benchmark data file validation
# ---------------------------------------------------------------------------


class TestBenchmarkFile:
    """Validate the benchmark JSON file structure."""

    def test_file_exists(self):
        assert BENCHMARKS_PATH.exists()

    def test_valid_json(self):
        data = json.loads(BENCHMARKS_PATH.read_text())
        assert "benchmarks" in data
        assert "version" in data

    def test_has_at_least_50_benchmarks(self):
        data = json.loads(BENCHMARKS_PATH.read_text())
        assert len(data["benchmarks"]) >= 50

    def test_each_benchmark_has_required_fields(self):
        data = json.loads(BENCHMARKS_PATH.read_text())
        for bm in data["benchmarks"]:
            assert "id" in bm, f"Missing id in benchmark"
            assert "scenario" in bm, f"Missing scenario in {bm.get('id')}"
            assert "parameters" in bm, f"Missing parameters in {bm.get('id')}"
            assert "expected" in bm, f"Missing expected in {bm.get('id')}"
            assert "tolerance_5pct" in bm, f"Missing tolerance_5pct in {bm.get('id')}"
            assert "tolerance_10pct" in bm, f"Missing tolerance_10pct in {bm.get('id')}"

    def test_ids_are_unique(self):
        data = json.loads(BENCHMARKS_PATH.read_text())
        ids = [bm["id"] for bm in data["benchmarks"]]
        assert len(ids) == len(set(ids))

    def test_tolerances_are_reasonable(self):
        data = json.loads(BENCHMARKS_PATH.read_text())
        for bm in data["benchmarks"]:
            t5 = bm["tolerance_5pct"]
            t10 = bm["tolerance_10pct"]
            assert t5[0] < t5[1], f"{bm['id']}: 5% range inverted"
            assert t10[0] < t10[1], f"{bm['id']}: 10% range inverted"
            assert t10[0] <= t5[0], f"{bm['id']}: 10% lower should be <= 5% lower"
            assert t10[1] >= t5[1], f"{bm['id']}: 10% upper should be >= 5% upper"


# ---------------------------------------------------------------------------
# 2. Benchmark schema model
# ---------------------------------------------------------------------------


class TestBenchmarkSchema:
    """Test the Pydantic schema for benchmarks."""

    def test_import_schema(self):
        from evaluation.validators.sample_size_validator import (
            Benchmark,
            BenchmarkSuite,
        )
        assert Benchmark is not None
        assert BenchmarkSuite is not None

    def test_load_benchmarks(self):
        from evaluation.validators.sample_size_validator import load_benchmarks

        suite = load_benchmarks()
        assert len(suite.benchmarks) >= 50

    def test_benchmark_has_expected_n(self):
        from evaluation.validators.sample_size_validator import load_benchmarks

        suite = load_benchmarks()
        for bm in suite.benchmarks:
            # Each benchmark must have at least one expected N value
            expected = bm.expected
            has_n = any(
                k in expected
                for k in [
                    "n_per_group",
                    "total_n",
                    "total_events",
                    "n_per_group_individual",
                    "n_control",
                ]
            )
            assert has_n, f"{bm.id} has no expected sample size value"


# ---------------------------------------------------------------------------
# 3. Scoring logic
# ---------------------------------------------------------------------------


class TestScoringLogic:
    """Test the concordance scoring functions."""

    def test_exact_match(self):
        from evaluation.validators.sample_size_validator import score_result

        result = score_result(actual=91, expected=91, tolerance_5pct=(87, 96), tolerance_10pct=(82, 100))
        assert result.exact_match is True
        assert result.within_5pct is True
        assert result.within_10pct is True

    def test_within_5pct(self):
        from evaluation.validators.sample_size_validator import score_result

        result = score_result(actual=89, expected=91, tolerance_5pct=(87, 96), tolerance_10pct=(82, 100))
        assert result.exact_match is False
        assert result.within_5pct is True
        assert result.within_10pct is True

    def test_within_10pct(self):
        from evaluation.validators.sample_size_validator import score_result

        result = score_result(actual=83, expected=91, tolerance_5pct=(87, 96), tolerance_10pct=(82, 100))
        assert result.exact_match is False
        assert result.within_5pct is False
        assert result.within_10pct is True

    def test_outside_tolerance(self):
        from evaluation.validators.sample_size_validator import score_result

        result = score_result(actual=50, expected=91, tolerance_5pct=(87, 96), tolerance_10pct=(82, 100))
        assert result.exact_match is False
        assert result.within_5pct is False
        assert result.within_10pct is False

    def test_deviation_pct_calculated(self):
        from evaluation.validators.sample_size_validator import score_result

        result = score_result(actual=100, expected=91, tolerance_5pct=(87, 96), tolerance_10pct=(82, 100))
        assert abs(result.deviation_pct - 9.89) < 0.1

    def test_zero_expected_handled(self):
        from evaluation.validators.sample_size_validator import score_result

        result = score_result(actual=5, expected=0, tolerance_5pct=(0, 0), tolerance_10pct=(0, 0))
        assert result.exact_match is False


# ---------------------------------------------------------------------------
# 4. Concordance summary
# ---------------------------------------------------------------------------


class TestConcordanceSummary:
    """Test the concordance summary computation."""

    def test_compute_concordance(self):
        from evaluation.validators.sample_size_validator import (
            ConcordanceSummary,
            ScoreResult,
            compute_concordance,
        )

        scores = [
            ScoreResult(benchmark_id="V01", actual=91, expected=91, exact_match=True, within_5pct=True, within_10pct=True, deviation_pct=0.0),
            ScoreResult(benchmark_id="V02", actual=60, expected=58, exact_match=False, within_5pct=True, within_10pct=True, deviation_pct=3.45),
            ScoreResult(benchmark_id="V03", actual=50, expected=29, exact_match=False, within_5pct=False, within_10pct=False, deviation_pct=72.4),
        ]
        summary = compute_concordance(scores)
        assert summary.total == 3
        assert summary.exact_match_count == 1
        assert summary.within_5pct_count == 2
        assert summary.within_10pct_count == 2
        assert abs(summary.exact_match_rate - 33.33) < 0.1
        assert abs(summary.within_5pct_rate - 66.67) < 0.1

    def test_empty_scores(self):
        from evaluation.validators.sample_size_validator import compute_concordance

        summary = compute_concordance([])
        assert summary.total == 0
        assert summary.exact_match_rate == 0.0


# ---------------------------------------------------------------------------
# 5. Report generation
# ---------------------------------------------------------------------------


class TestValidationReport:
    """Test the validation report generator."""

    def test_generate_report_returns_string(self):
        from evaluation.validators.sample_size_validator import (
            ConcordanceSummary,
            ScoreResult,
            generate_validation_report,
        )

        scores = [
            ScoreResult(benchmark_id="V01", actual=91, expected=91, exact_match=True, within_5pct=True, within_10pct=True, deviation_pct=0.0),
        ]
        summary = ConcordanceSummary(
            total=1, exact_match_count=1, within_5pct_count=1, within_10pct_count=1,
            exact_match_rate=100.0, within_5pct_rate=100.0, within_10pct_rate=100.0,
            mean_deviation_pct=0.0, median_deviation_pct=0.0,
        )
        report = generate_validation_report(scores, summary)
        assert isinstance(report, str)
        assert "V01" in report
        assert "Concordance" in report or "concordance" in report.lower()

    def test_report_contains_table(self):
        from evaluation.validators.sample_size_validator import (
            ConcordanceSummary,
            ScoreResult,
            generate_validation_report,
        )

        scores = [
            ScoreResult(benchmark_id="V01", actual=91, expected=91, exact_match=True, within_5pct=True, within_10pct=True, deviation_pct=0.0),
            ScoreResult(benchmark_id="V02", actual=60, expected=58, exact_match=False, within_5pct=True, within_10pct=True, deviation_pct=3.45),
        ]
        summary = ConcordanceSummary(
            total=2, exact_match_count=1, within_5pct_count=2, within_10pct_count=2,
            exact_match_rate=50.0, within_5pct_rate=100.0, within_10pct_rate=100.0,
            mean_deviation_pct=1.72, median_deviation_pct=1.72,
        )
        report = generate_validation_report(scores, summary)
        # Should contain a markdown table
        assert "|" in report
        assert "---" in report
