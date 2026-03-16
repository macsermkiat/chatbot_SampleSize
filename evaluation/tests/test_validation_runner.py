"""Tests for the validation runner components (prompt generator, extractor, runner)."""

from __future__ import annotations

import pytest

from evaluation.validators.prompt_generator import generate_prompt
from evaluation.validators.sample_size_extractor import (
    ExtractedN,
    extract_sample_size,
)
from evaluation.validators.sample_size_validator import load_benchmarks


# ---------------------------------------------------------------------------
# 1. Prompt generator tests
# ---------------------------------------------------------------------------


class TestPromptGenerator:
    """Test that prompts are generated for all benchmark types."""

    def test_two_sample_t_test(self):
        prompt = generate_prompt("V01", {
            "test_type": "two_sample_t_test",
            "alpha": 0.05,
            "power": 0.80,
            "mean_difference": 5.0,
            "sd": 12.0,
            "sides": 2,
            "allocation_ratio": 1.0,
        })
        assert "two-sample t-test" in prompt.lower()
        assert "0.05" in prompt
        assert "0.8" in prompt

    def test_one_sample_t_test(self):
        prompt = generate_prompt("V21", {
            "test_type": "one_sample_t_test",
            "alpha": 0.05,
            "power": 0.80,
            "mean_h0": 200,
            "mean_h1": 210,
            "sd": 30,
            "sides": 2,
        })
        assert "one-sample t-test" in prompt.lower()
        assert "200" in prompt

    def test_survival(self):
        prompt = generate_prompt("V08", {
            "test_type": "survival_log_rank",
            "alpha": 0.05,
            "power": 0.80,
            "hazard_ratio": 0.75,
            "sides": 2,
        })
        assert "survival" in prompt.lower() or "log-rank" in prompt.lower()
        assert "0.75" in prompt

    def test_non_inferiority_proportions(self):
        prompt = generate_prompt("V28", {
            "test_type": "non_inferiority_proportions",
            "alpha": 0.025,
            "power": 0.80,
            "p_reference": 0.70,
            "p_test": 0.70,
            "non_inferiority_margin": 0.10,
            "sides": 1,
        })
        assert "non-inferiority" in prompt.lower()

    def test_crossover(self):
        prompt = generate_prompt("V47", {
            "test_type": "crossover_2x2",
            "alpha": 0.05,
            "power": 0.80,
            "mean_difference": 3.0,
            "sd_within": 8.0,
            "correlation": 0.60,
            "sides": 2,
        })
        assert "crossover" in prompt.lower()

    def test_all_benchmarks_generate_prompts(self):
        """Every benchmark should produce a non-empty prompt."""
        suite = load_benchmarks()
        for bm in suite.benchmarks:
            prompt = generate_prompt(bm.id, bm.parameters)
            assert len(prompt) > 20, f"{bm.id} generated too-short prompt: {prompt}"

    def test_one_sided_noted(self):
        prompt = generate_prompt("V24", {
            "test_type": "two_sample_t_test",
            "alpha": 0.05,
            "power": 0.80,
            "effect_size_d": 0.50,
            "sides": 1,
            "allocation_ratio": 1.0,
        })
        assert "one-sided" in prompt.lower()

    def test_unequal_allocation_noted(self):
        prompt = generate_prompt("V19", {
            "test_type": "two_sample_t_test",
            "alpha": 0.05,
            "power": 0.80,
            "mean_difference": 3.0,
            "sd": 10.0,
            "sides": 2,
            "allocation_ratio": 2.0,
        })
        assert "2:1" in prompt or "allocation" in prompt.lower()


# ---------------------------------------------------------------------------
# 2. Sample size extractor tests
# ---------------------------------------------------------------------------


class TestSampleSizeExtractor:
    """Test extraction of N from various response formats."""

    def test_extract_from_n_equals(self):
        result = extract_sample_size(
            response_text="The required sample size is N = 91 per group.",
            code_output="",
            execution_result="",
            expected_keys={"n_per_group": 91},
        )
        assert result is not None
        assert result.value == 91

    def test_extract_from_execution_result(self):
        result = extract_sample_size(
            response_text="Working on it...",
            code_output="n = solve_power(...)",
            execution_result="N per group = 91",
            expected_keys={"n_per_group": 91},
        )
        assert result is not None
        assert result.value == 91
        assert result.source == "execution_result"

    def test_extract_events(self):
        result = extract_sample_size(
            response_text="You need approximately 380 events.",
            code_output="",
            execution_result="",
            expected_keys={"total_events": 380},
        )
        assert result is not None
        assert result.value == 380

    def test_extract_from_table(self):
        result = extract_sample_size(
            response_text="| Parameter | Value |\n|---|---|\n| N per group | 91 |",
            code_output="",
            execution_result="",
            expected_keys={"n_per_group": 91},
        )
        assert result is not None
        assert result.value == 91

    def test_extract_total_n(self):
        result = extract_sample_size(
            response_text="Total sample size is 182 participants.",
            code_output="",
            execution_result="",
            expected_keys={"total_n": 182},
        )
        assert result is not None
        assert result.value == 182

    def test_extract_with_comma(self):
        result = extract_sample_size(
            response_text="You need 1,189 events.",
            code_output="",
            execution_result="",
            expected_keys={"total_events": 1189},
        )
        assert result is not None
        assert result.value == 1189

    def test_returns_none_when_no_match(self):
        result = extract_sample_size(
            response_text="I need more information to calculate this.",
            code_output="",
            execution_result="",
            expected_keys={"n_per_group": 91},
        )
        assert result is None

    def test_prefers_execution_result(self):
        """Execution result should take priority over response text."""
        result = extract_sample_size(
            response_text="N = 100 per group",
            code_output="",
            execution_result="N per group = 91",
            expected_keys={"n_per_group": 91},
        )
        assert result is not None
        assert result.value == 91
        assert result.source == "execution_result"

    def test_rejects_unreasonable_values(self):
        """Values outside 2-100000 should be rejected."""
        result = extract_sample_size(
            response_text="N = 1",
            code_output="",
            execution_result="",
            expected_keys={"n_per_group": 91},
        )
        assert result is None

    def test_extract_participants_needed(self):
        result = extract_sample_size(
            response_text="You will need approximately 126 participants.",
            code_output="",
            execution_result="",
            expected_keys={"total_n": 126},
        )
        assert result is not None
        assert result.value == 126

    def test_extract_subjects_per_group(self):
        result = extract_sample_size(
            response_text="45 subjects per group are required.",
            code_output="",
            execution_result="",
            expected_keys={"n_per_group": 45},
        )
        assert result is not None


# ---------------------------------------------------------------------------
# 3. Integration: prompt -> expected extraction key alignment
# ---------------------------------------------------------------------------


class TestPromptBenchmarkAlignment:
    """Verify prompts ask for the right thing based on benchmark type."""

    def test_survival_asks_for_events(self):
        prompt = generate_prompt("V08", {
            "test_type": "survival_log_rank",
            "alpha": 0.05,
            "power": 0.80,
            "hazard_ratio": 0.75,
            "sides": 2,
        })
        assert "events" in prompt.lower()

    def test_cluster_asks_for_individuals_and_clusters(self):
        prompt = generate_prompt("V15", {
            "test_type": "cluster_randomized_proportions",
            "alpha": 0.05,
            "power": 0.80,
            "p1": 0.40,
            "p2": 0.25,
            "icc": 0.05,
            "cluster_size": 50,
            "sides": 2,
        })
        assert "cluster" in prompt.lower()

    def test_paired_asks_for_pairs(self):
        prompt = generate_prompt("V03", {
            "test_type": "paired_t_test",
            "alpha": 0.05,
            "power": 0.80,
            "mean_difference": 8.0,
            "sd_difference": 15.0,
            "sides": 2,
        })
        assert "pair" in prompt.lower()
