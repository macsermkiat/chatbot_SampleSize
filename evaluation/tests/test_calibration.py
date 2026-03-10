"""Tests for LLM judge calibration and consistency measurement."""

from evaluation.llm_judge.calibration import (
    CalibrationResult,
    ConsistencyMetrics,
    compute_self_consistency,
    evaluate_gold_standards,
    check_score_distribution,
    GOLD_STANDARDS,
)
from evaluation.rubrics.schema import DimensionScore, EvaluationResult


def _make_result(
    case_id: str,
    system_id: str,
    judge_run: int,
    scores: dict[str, int],
    overall: int = 3,
) -> EvaluationResult:
    return EvaluationResult(
        case_id=case_id,
        system_id=system_id,
        judge_run=judge_run,
        rubric_id="test",
        dimension_scores=[
            DimensionScore(dimension_id=dim_id, score=score)
            for dim_id, score in scores.items()
        ],
        overall_quality=overall,
    )


class TestSelfConsistency:
    def test_perfect_consistency(self):
        results = [
            _make_result("C01", "system_a", run, {"D1": 4, "D2": 3})
            for run in range(1, 4)
        ]
        metrics = compute_self_consistency(results)
        d1 = next(m for m in metrics if m.dimension_id == "D1")
        assert d1.exact_agreement_rate == 1.0
        assert d1.within_one_rate == 1.0

    def test_no_consistency(self):
        results = [
            _make_result("C01", "system_a", 1, {"D1": 1}),
            _make_result("C01", "system_a", 2, {"D1": 5}),
            _make_result("C01", "system_a", 3, {"D1": 3}),
        ]
        metrics = compute_self_consistency(results)
        d1 = next(m for m in metrics if m.dimension_id == "D1")
        assert d1.exact_agreement_rate == 0.0

    def test_within_one_partial(self):
        results = [
            _make_result("C01", "system_a", 1, {"D1": 3}),
            _make_result("C01", "system_a", 2, {"D1": 4}),
            _make_result("C01", "system_a", 3, {"D1": 3}),
        ]
        metrics = compute_self_consistency(results)
        d1 = next(m for m in metrics if m.dimension_id == "D1")
        # Pairs: (3,4), (3,3), (4,3) -> within_one all True
        assert d1.within_one_rate == 1.0

    def test_empty_results(self):
        metrics = compute_self_consistency([])
        assert metrics == []


class TestGoldStandardCalibration:
    def test_perfect_calibration(self):
        cal_results = [
            CalibrationResult(
                gold_case_id="gold_01",
                dimension_id="M1",
                expected_score=5,
                judge_score=5,
                is_exact_match=True,
                is_within_one=True,
            ),
            CalibrationResult(
                gold_case_id="gold_02",
                dimension_id="M1",
                expected_score=1,
                judge_score=1,
                is_exact_match=True,
                is_within_one=True,
            ),
        ]
        report = evaluate_gold_standards(cal_results)
        assert report.exact_match_rate == 1.0
        assert report.within_one_rate == 1.0
        assert report.passed

    def test_failing_calibration(self):
        cal_results = [
            CalibrationResult(
                gold_case_id="gold_01",
                dimension_id="M1",
                expected_score=5,
                judge_score=2,
                is_exact_match=False,
                is_within_one=False,
            ),
        ]
        report = evaluate_gold_standards(cal_results, threshold=0.80)
        assert not report.passed
        assert report.within_one_rate == 0.0

    def test_empty_calibration(self):
        report = evaluate_gold_standards([])
        assert not report.passed
        assert report.total_cases == 0


class TestScoreDistribution:
    def test_detects_distribution(self):
        results = [
            _make_result("C01", "system_a", 1, {"D1": 3}),
            _make_result("C02", "system_a", 1, {"D1": 3}),
            _make_result("C03", "system_a", 1, {"D1": 4}),
        ]
        dist = check_score_distribution(results)
        assert dist["D1"][3] == 2
        assert dist["D1"][4] == 1


class TestGoldStandards:
    def test_gold_standards_exist(self):
        assert len(GOLD_STANDARDS) >= 5

    def test_gold_standards_have_required_fields(self):
        for gs in GOLD_STANDARDS:
            assert "gold_id" in gs
            assert "dimension_id" in gs
            assert "expected_score" in gs
            assert "response_text" in gs
            assert 1 <= gs["expected_score"] <= 5
