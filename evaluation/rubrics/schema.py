"""Rubric schema definitions for evaluation scoring."""

from __future__ import annotations

from datetime import datetime, timezone

from pydantic import BaseModel, Field


class ScoreAnchor(BaseModel):
    """Descriptive anchor for a specific score level."""

    score: int = Field(..., ge=1, le=5)
    label: str = Field(..., description="Short label, e.g. 'Poor', 'Excellent'")
    description: str = Field(
        ..., description="Detailed description of what this score level means"
    )


class RubricDimension(BaseModel):
    """A single evaluation dimension with anchored scoring."""

    dimension_id: str = Field(..., description="Unique ID, e.g. 'M1' or 'B3'")
    name: str = Field(..., description="Human-readable dimension name")
    description: str = Field(
        ..., description="What this dimension measures"
    )
    weight: float = Field(
        default=1.0, description="Weight for composite score calculation"
    )
    anchors: list[ScoreAnchor] = Field(
        ..., min_length=5, max_length=5,
        description="Exactly 5 anchors (score 1 through 5)",
    )

    def anchor_text(self) -> str:
        """Format anchors as text for judge prompts."""
        lines = []
        for a in sorted(self.anchors, key=lambda x: x.score):
            lines.append(f"  {a.score} ({a.label}): {a.description}")
        return "\n".join(lines)


class Rubric(BaseModel):
    """A complete rubric with multiple dimensions."""

    rubric_id: str
    name: str
    description: str
    dimensions: list[RubricDimension]

    def get_dimension(self, dimension_id: str) -> RubricDimension | None:
        return next(
            (d for d in self.dimensions if d.dimension_id == dimension_id), None
        )


class DimensionScore(BaseModel):
    """Score for a single dimension from a single evaluator/judge run."""

    dimension_id: str
    score: int = Field(..., ge=1, le=5)
    reasoning: str = Field(
        default="", description="Why this score was given"
    )
    evidence: str = Field(
        default="", description="Specific text from response supporting the score"
    )


class EvaluationResult(BaseModel):
    """Complete evaluation of one response by one judge run."""

    case_id: str
    system_id: str = Field(
        ..., description="Blinded label: 'system_a' or 'system_b'"
    )
    judge_run: int = Field(
        ..., ge=1, description="Which run (1, 2, or 3) for consistency"
    )
    rubric_id: str
    dimension_scores: list[DimensionScore]
    overall_quality: int = Field(..., ge=1, le=5)
    overall_reasoning: str = ""
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    @property
    def composite_score(self) -> float:
        if not self.dimension_scores:
            return 0.0
        return sum(s.score for s in self.dimension_scores) / len(
            self.dimension_scores
        )


class CaseComparison(BaseModel):
    """Side-by-side comparison results for a single case."""

    case_id: str
    system_a_results: list[EvaluationResult] = Field(
        default_factory=list, description="All judge runs for system A"
    )
    system_b_results: list[EvaluationResult] = Field(
        default_factory=list, description="All judge runs for system B"
    )
    system_a_identity: str = Field(
        default="", description="Revealed after evaluation: 'chatbot' or 'gpt5'"
    )
    system_b_identity: str = Field(
        default="", description="Revealed after evaluation: 'chatbot' or 'gpt5'"
    )
