"""Tests for rubric schemas and definitions."""

from evaluation.rubrics.schema import (
    DimensionScore,
    EvaluationResult,
    Rubric,
    RubricDimension,
    ScoreAnchor,
)
from evaluation.rubrics.methodology_rubric import METHODOLOGY_RUBRIC
from evaluation.rubrics.biostatistics_rubric import BIOSTATISTICS_RUBRIC


class TestRubricSchema:
    def test_score_anchor_validation(self):
        anchor = ScoreAnchor(score=3, label="Adequate", description="Meets basic expectations")
        assert anchor.score == 3
        assert anchor.label == "Adequate"

    def test_dimension_anchor_text(self):
        dim = RubricDimension(
            dimension_id="T1",
            name="Test Dimension",
            description="For testing",
            anchors=[
                ScoreAnchor(score=i, label=f"Level {i}", description=f"Desc {i}")
                for i in range(1, 6)
            ],
        )
        text = dim.anchor_text()
        assert "1 (Level 1)" in text
        assert "5 (Level 5)" in text

    def test_evaluation_result_composite_score(self):
        result = EvaluationResult(
            case_id="T01",
            system_id="system_a",
            judge_run=1,
            rubric_id="test",
            dimension_scores=[
                DimensionScore(dimension_id="D1", score=4),
                DimensionScore(dimension_id="D2", score=2),
            ],
            overall_quality=3,
        )
        assert result.composite_score == 3.0

    def test_evaluation_result_empty_composite(self):
        result = EvaluationResult(
            case_id="T01",
            system_id="system_a",
            judge_run=1,
            rubric_id="test",
            dimension_scores=[],
            overall_quality=3,
        )
        assert result.composite_score == 0.0


class TestMethodologyRubric:
    def test_has_8_dimensions(self):
        assert len(METHODOLOGY_RUBRIC.dimensions) == 8

    def test_dimension_ids(self):
        ids = [d.dimension_id for d in METHODOLOGY_RUBRIC.dimensions]
        expected = ["M1", "M2", "M3", "M4", "M5", "M6", "M7", "M8"]
        assert ids == expected

    def test_each_dimension_has_5_anchors(self):
        for dim in METHODOLOGY_RUBRIC.dimensions:
            assert len(dim.anchors) == 5, f"{dim.dimension_id} has {len(dim.anchors)} anchors"

    def test_get_dimension(self):
        dim = METHODOLOGY_RUBRIC.get_dimension("M3")
        assert dim is not None
        assert "Causal" in dim.name

    def test_get_nonexistent_dimension(self):
        dim = METHODOLOGY_RUBRIC.get_dimension("X99")
        assert dim is None

    def test_weighted_dimensions(self):
        m3 = METHODOLOGY_RUBRIC.get_dimension("M3")
        m5 = METHODOLOGY_RUBRIC.get_dimension("M5")
        assert m3.weight == 1.5  # Causal inference is weighted higher
        assert m5.weight == 0.75  # Ethics is weighted lower


class TestBiostatisticsRubric:
    def test_has_8_dimensions(self):
        assert len(BIOSTATISTICS_RUBRIC.dimensions) == 8

    def test_dimension_ids(self):
        ids = [d.dimension_id for d in BIOSTATISTICS_RUBRIC.dimensions]
        expected = ["B1", "B2", "B3", "B4", "B5", "B6", "B7", "B8"]
        assert ids == expected

    def test_each_dimension_has_5_anchors(self):
        for dim in BIOSTATISTICS_RUBRIC.dimensions:
            assert len(dim.anchors) == 5, f"{dim.dimension_id} has {len(dim.anchors)} anchors"

    def test_weighted_dimensions(self):
        b1 = BIOSTATISTICS_RUBRIC.get_dimension("B1")
        b8 = BIOSTATISTICS_RUBRIC.get_dimension("B8")
        assert b1.weight == 1.5
        assert b8.weight == 0.75
