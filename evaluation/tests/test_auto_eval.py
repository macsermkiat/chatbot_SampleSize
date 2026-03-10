"""Tests for automated evaluation components."""

from evaluation.auto_eval.test_checker import check_statistical_test
from evaluation.auto_eval.completeness_checker import check_completeness
from evaluation.auto_eval.code_validator import _check_syntax, _sanitize_code


class TestStatisticalTestChecker:
    def test_exact_match(self):
        result = check_statistical_test(
            case_id="B01",
            system_id="chatbot",
            response_text="We recommend using an independent two-sample t-test for this comparison.",
            expected_test="independent two-sample t-test",
        )
        assert result.is_correct
        assert result.confidence > 0.5

    def test_synonym_match(self):
        result = check_statistical_test(
            case_id="B01",
            system_id="chatbot",
            response_text="A Wilcoxon rank-sum test is appropriate here.",
            expected_test="Mann-Whitney U test",
        )
        assert result.is_correct
        assert "rank-sum" in result.matched_synonym

    def test_no_match(self):
        result = check_statistical_test(
            case_id="B01",
            system_id="chatbot",
            response_text="You should use a bar chart to visualize the data.",
            expected_test="independent two-sample t-test",
        )
        assert not result.is_correct
        assert result.detected_test == ""

    def test_custom_synonyms(self):
        result = check_statistical_test(
            case_id="B01",
            system_id="chatbot",
            response_text="Use the super special custom test.",
            expected_test="some test",
            accepted_synonyms=["super special custom test"],
        )
        assert result.is_correct

    def test_chi_square_variants(self):
        for variant in ["chi-square", "chi-squared", "chi square"]:
            result = check_statistical_test(
                case_id="B02",
                system_id="gpt5",
                response_text=f"Apply the {variant} test of independence.",
                expected_test="chi-square test",
            )
            assert result.is_correct, f"Failed for variant: {variant}"

    def test_cox_model_detection(self):
        result = check_statistical_test(
            case_id="B03",
            system_id="chatbot",
            response_text="A Cox proportional hazards regression model should be fitted.",
            expected_test="Cox proportional hazards",
        )
        assert result.is_correct


class TestCompletenessChecker:
    def test_full_pico_detection(self):
        text = (
            "The population includes adult patients with diabetes. "
            "The intervention is metformin therapy compared to placebo as control. "
            "The primary outcome is HbA1c reduction over a 12-month follow-up duration. "
            "The setting is a tertiary hospital."
        )
        result = check_completeness("M01", "chatbot", text)
        assert result.pico_elements_found["P"]
        assert result.pico_elements_found["I"]
        assert result.pico_elements_found["C"]
        assert result.pico_elements_found["O"]
        assert result.pico_elements_found["T"]
        assert result.pico_elements_found["S"]
        assert result.pico_completeness == 1.0

    def test_partial_pico(self):
        text = "The patients in this study receive treatment."
        result = check_completeness("M01", "chatbot", text)
        assert result.pico_elements_found["P"]
        assert result.pico_elements_found["I"]
        assert result.pico_completeness < 1.0

    def test_bias_detection(self):
        text = "Watch for selection bias, information bias, and immortal time bias."
        result = check_completeness("M01", "chatbot", text)
        assert result.mentions_bias
        assert result.bias_count == 3
        assert "selection bias" in result.biases_found

    def test_equator_guideline_detection(self):
        text = "Follow the STROBE checklist for this observational study."
        result = check_completeness("M01", "chatbot", text)
        assert result.mentions_equator
        assert result.equator_guideline_found == "STROBE"

    def test_ethics_detection(self):
        text = "IRB approval and informed consent are required."
        result = check_completeness("M01", "chatbot", text)
        assert result.mentions_ethics

    def test_code_block_detection(self):
        text = "Here is the code:\n```python\nprint('hello')\n```"
        result = check_completeness("B01", "chatbot", text)
        assert result.has_code_block

    def test_word_count(self):
        text = "one two three four five"
        result = check_completeness("T01", "test", text)
        assert result.total_word_count == 5

    def test_multi_turn_pico_aggregation(self):
        """PICO elements split across turns should all be detected."""
        turn1 = "The population includes adult patients with diabetes."
        turn2 = (
            "The intervention is metformin therapy compared to placebo as control. "
            "The primary outcome is HbA1c reduction over a 12-month follow-up duration. "
            "The setting is a tertiary hospital."
        )
        result = check_completeness(
            "M01", "chatbot", turn1,
            additional_response_texts=[turn2],
        )
        assert result.pico_elements_found["P"]
        assert result.pico_elements_found["I"]
        assert result.pico_elements_found["C"]
        assert result.pico_elements_found["O"]
        assert result.pico_elements_found["T"]
        assert result.pico_elements_found["S"]
        assert result.pico_completeness == 1.0

    def test_multi_turn_word_count(self):
        """Word count should sum across all turns."""
        result = check_completeness(
            "T01", "test", "one two three",
            additional_response_texts=["four five"],
        )
        # "one two three" + "\n\n" + "four five" => 5 words + 0 (whitespace)
        assert result.total_word_count == 5

    def test_multi_turn_code_detection(self):
        """Code block in a follow-up turn should be detected."""
        turn1 = "Use a t-test."
        turn2 = "Here is the code:\n```python\nprint('hello')\n```"
        result = check_completeness(
            "B01", "chatbot", turn1,
            additional_response_texts=[turn2],
        )
        assert result.has_code_block

    def test_multi_turn_bias_aggregation(self):
        """Biases mentioned across turns should all be counted."""
        turn1 = "Watch out for selection bias."
        turn2 = "Also consider information bias and immortal time bias."
        result = check_completeness(
            "M01", "chatbot", turn1,
            additional_response_texts=[turn2],
        )
        assert result.mentions_bias
        assert result.bias_count == 3
        assert "selection bias" in result.biases_found
        assert "immortal time bias" in result.biases_found


class TestCodeValidator:
    def test_valid_syntax(self):
        assert _check_syntax("x = 1 + 2\nprint(x)")

    def test_invalid_syntax(self):
        assert not _check_syntax("def broken(:\n  pass")

    def test_sanitize_removes_pip(self):
        code = "import numpy\npip install pandas\nprint(1)"
        sanitized = _sanitize_code(code)
        assert "REMOVED" in sanitized
        assert "pip install" not in sanitized.replace("REMOVED: pip install pandas", "")

    def test_sanitize_removes_subprocess(self):
        code = "import subprocess\nsubprocess.run(['ls'])"
        sanitized = _sanitize_code(code)
        assert sanitized.count("REMOVED") == 2

    def test_sanitize_preserves_safe_code(self):
        code = "import numpy as np\nresult = np.mean([1, 2, 3])\nprint(result)"
        sanitized = _sanitize_code(code)
        assert "REMOVED" not in sanitized
        assert sanitized == code
