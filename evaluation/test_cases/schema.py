"""Test case and ground truth schemas for evaluation."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class MethodologyGroundTruth(BaseModel):
    """Expected elements in a correct methodology response."""

    study_design: str = Field(
        ..., description="Expected study design, e.g. 'retrospective cohort'"
    )
    pico_elements: dict[str, str] = Field(
        default_factory=dict,
        description="Expected PICOTS elements: P, I, C, O, T, S",
    )
    biases_to_identify: list[str] = Field(
        default_factory=list,
        description="Biases the response should mention, e.g. ['immortal time bias']",
    )
    equator_guideline: str = Field(
        default="", description="Expected EQUATOR guideline, e.g. 'STROBE'"
    )
    causal_framework: str = Field(
        default="",
        description="Expected causal framework, e.g. 'Target Trial Emulation'",
    )
    ethical_considerations: list[str] = Field(
        default_factory=list,
        description="Key ethical points to address",
    )
    key_confounders: list[str] = Field(
        default_factory=list,
        description="Confounders the response should identify",
    )


class BiostatisticsGroundTruth(BaseModel):
    """Expected elements in a correct biostatistics response."""

    correct_statistical_test: str = Field(
        ..., description="The correct test, e.g. 'Cox proportional hazards'"
    )
    test_synonyms: list[str] = Field(
        default_factory=list,
        description="Acceptable synonyms for the correct test",
    )
    sample_size_range: tuple[int, int] = Field(
        default=(0, 0),
        description="Acceptable sample size range (min, max) per group",
    )
    required_parameters: dict[str, str] = Field(
        default_factory=dict,
        description="Parameters needed: alpha, power, effect_size, etc.",
    )
    required_assumptions: list[str] = Field(
        default_factory=list,
        description="Statistical assumptions to check",
    )
    expected_code_output_pattern: str = Field(
        default="",
        description="Regex pattern to match against code output",
    )
    formula_name: str = Field(
        default="",
        description="Expected formula/method name for sample size calculation",
    )


class TestCase(BaseModel):
    """A single evaluation test case."""

    case_id: str = Field(..., description="Unique identifier, e.g. 'M01' or 'B05'")
    agent_target: Literal["methodology", "biostatistics"] = Field(
        ..., description="Which agent this case targets"
    )
    specialty: str = Field(..., description="Medical specialty, e.g. 'cardiology'")
    complexity: Literal["basic", "intermediate", "advanced"] = Field(
        ..., description="Scenario complexity level"
    )
    expertise_mode: Literal["simple", "advanced"] = Field(
        ..., description="Expertise level to send with request"
    )
    prompt: str = Field(..., description="The user message to send")
    follow_up_prompts: list[str] = Field(
        default_factory=list,
        description="Follow-up messages for multi-turn scenarios",
    )
    methodology_ground_truth: MethodologyGroundTruth | None = None
    biostatistics_ground_truth: BiostatisticsGroundTruth | None = None
    clinical_context: str = Field(
        default="",
        description="Background context for evaluators to understand the case",
    )
    rationale: str = Field(
        default="",
        description="Why this case tests what it tests",
    )


class TestCaseBank(BaseModel):
    """Collection of all test cases."""

    version: str = "1.0.0"
    cases: list[TestCase]

    def filter_by_agent(self, agent: str) -> list[TestCase]:
        return [c for c in self.cases if c.agent_target == agent]

    def filter_by_complexity(self, complexity: str) -> list[TestCase]:
        return [c for c in self.cases if c.complexity == complexity]

    def filter_by_expertise(self, mode: str) -> list[TestCase]:
        return [c for c in self.cases if c.expertise_mode == mode]
