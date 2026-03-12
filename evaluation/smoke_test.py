"""Smoke test: run 3 cases through the full pipeline with synthetic responses.

This script validates the evaluation framework wiring without requiring
a running backend or API keys. It:
  1. Loads 3 real test cases (1 methodology, 1 biostatistics, 1 edge)
  2. Generates realistic synthetic responses for "chatbot" and "gpt5"
  3. Saves them via the response store
  4. Runs automated evaluation (test checker, completeness, code validator)
  5. Runs blinding and pair creation
  6. Optionally runs the LLM judge (if ANTHROPIC_API_KEY is set)
  7. Prints a summary report

Usage:
    cd /path/to/chatbot_SampleSize
    backend/.venv/bin/python -m evaluation.smoke_test
    backend/.venv/bin/python -m evaluation.smoke_test --with-judge   # includes LLM judge
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
import tempfile
from dataclasses import asdict
from pathlib import Path

from evaluation.config import EvalConfig
from evaluation.test_cases.schema import TestCase
from evaluation.collectors.chatbot_collector import CollectedResponse
from evaluation.collectors.response_store import (
    get_responses_by_case,
    load_responses,
    save_responses,
)
from evaluation.auto_eval.test_checker import check_statistical_test
from evaluation.auto_eval.completeness_checker import check_completeness
from evaluation.auto_eval.code_validator import validate_code
from evaluation.llm_judge.blinding import create_blinded_pairs

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("smoke_test")

# ---------------------------------------------------------------------------
# Test case IDs to use
# ---------------------------------------------------------------------------
SMOKE_CASE_IDS = ("M01", "B01", "E02")


# ---------------------------------------------------------------------------
# Synthetic response generators
# ---------------------------------------------------------------------------

SYNTHETIC_CHATBOT_RESPONSES: dict[str, list[dict]] = {
    "M01": [
        {
            "turn": 1,
            "text": (
                "## Study Design Recommendation\n\n"
                "For your question about whether aspirin prevents heart attacks, "
                "I recommend a **randomized controlled trial (RCT)**.\n\n"
                "### PICO Framework\n"
                "- **Population**: Adult patients at risk of cardiovascular events\n"
                "- **Intervention**: Aspirin therapy (e.g., 100mg daily)\n"
                "- **Comparator**: Placebo control\n"
                "- **Outcome**: Incidence of myocardial infarction\n"
                "- **Timeframe**: 5-year follow-up period\n"
                "- **Setting**: Primary care or cardiology clinic\n\n"
                "### Key Biases to Address\n"
                "Be aware of **selection bias** during randomization, "
                "**attrition bias** from patient dropout, and "
                "**performance bias** if blinding is inadequate.\n\n"
                "### Reporting Standard\n"
                "Follow the **CONSORT** checklist for reporting your RCT.\n\n"
                "### Ethical Considerations\n"
                "Ensure clinical equipoise exists and obtain informed consent "
                "from all participants. IRB approval is required.\n\n"
                "### Next Steps\n"
                "1. Define your inclusion/exclusion criteria precisely\n"
                "2. Calculate required sample size\n"
                "3. Design your randomization scheme\n"
                "4. Submit to IRB for ethics approval"
            ),
            "code": "",
        },
    ],
    "B01": [
        {
            "turn": 1,
            "text": (
                "## Sample Size Calculation\n\n"
                "For comparing mean blood pressure between two groups, you need "
                "an **independent two-sample t-test**.\n\n"
                "### Parameters\n"
                "- Clinically meaningful difference: 10 mmHg\n"
                "- Standard deviation: 20 mmHg\n"
                "- Cohen's d = 10/20 = 0.5 (medium effect)\n"
                "- Alpha: 0.05 (two-sided)\n"
                "- Power: 0.80\n\n"
                "### Assumptions\n"
                "This assumes **normality** of blood pressure distributions, "
                "**equal variances** between groups, and **independence** of "
                "observations.\n\n"
                "### Result\n"
                "You need approximately **64 patients per group** (128 total).\n\n"
                "This is based on the standard power analysis formula for two "
                "independent means using Cohen's d."
            ),
            "code": "",
        },
        {
            "turn": 2,
            "text": (
                "Here is the Python code for the sample size calculation:\n\n"
                "```python\n"
                "from scipy import stats\n"
                "import math\n\n"
                "# Parameters\n"
                "d = 0.5       # Cohen's d = 10 / 20\n"
                "alpha = 0.05  # two-sided\n"
                "power = 0.80\n\n"
                "# Sample size per group\n"
                "z_alpha = stats.norm.ppf(1 - alpha / 2)\n"
                "z_beta = stats.norm.ppf(power)\n"
                "n = math.ceil(2 * ((z_alpha + z_beta) / d) ** 2)\n"
                "print(f'{n} per group')\n"
                "```\n"
            ),
            "code": (
                "from scipy import stats\n"
                "import math\n\n"
                "d = 0.5\n"
                "alpha = 0.05\n"
                "power = 0.80\n\n"
                "z_alpha = stats.norm.ppf(1 - alpha / 2)\n"
                "z_beta = stats.norm.ppf(power)\n"
                "n = math.ceil(2 * ((z_alpha + z_beta) / d) ** 2)\n"
                "print(f'{n} per group')\n"
            ),
        },
    ],
    "E02": [
        {
            "turn": 1,
            "text": (
                "I'd be happy to help you design your research study. However, "
                "I need a bit more information to provide specific guidance.\n\n"
                "Could you please clarify:\n"
                "1. What is the target population?\n"
                "2. What intervention or exposure are you studying?\n"
                "3. What is the primary outcome you're measuring?\n"
                "4. What comparison group will you use?"
            ),
            "code": "",
        },
        {
            "turn": 2,
            "text": (
                "Thank you for the clarification. For comparing SGLT2 inhibitors "
                "versus placebo for HbA1c reduction in adults with type 2 diabetes, "
                "I recommend:\n\n"
                "### Study Design\n"
                "A **randomized controlled trial** is most appropriate.\n\n"
                "### PICO Framework\n"
                "- **Population**: Adults with type 2 diabetes (T2DM)\n"
                "- **Intervention**: SGLT2 inhibitor therapy\n"
                "- **Comparator**: Placebo\n"
                "- **Outcome**: HbA1c reduction over 12 months\n"
                "- **Setting**: Tertiary hospital or multi-center\n\n"
                "### Reporting\n"
                "Follow the CONSORT guidelines for your trial report."
            ),
            "code": "",
        },
    ],
}

SYNTHETIC_GPT5_RESPONSES: dict[str, list[dict]] = {
    "M01": [
        {
            "turn": 1,
            "text": (
                "To study whether aspirin prevents heart attacks, you should "
                "consider a randomized controlled trial. This would involve "
                "randomly assigning participants to either aspirin or placebo "
                "groups and following them over time to measure heart attack "
                "rates.\n\n"
                "Key considerations:\n"
                "- Sample size should be large enough for statistical power\n"
                "- Double-blinding is important\n"
                "- Follow up should be at least several years\n"
                "- Consider patient compliance and dropout"
            ),
            "code": "",
        },
    ],
    "B01": [
        {
            "turn": 1,
            "text": (
                "For comparing blood pressure between two groups, you can use "
                "a two-sample t-test. With a difference of 10 mmHg and standard "
                "deviation of 20 mmHg, you need about 64 patients per group.\n\n"
                "The calculation uses the formula for comparing two means with "
                "80% power and a significance level of 0.05."
            ),
            "code": "",
        },
        {
            "turn": 2,
            "text": (
                "Here's the Python code:\n\n"
                "```python\n"
                "import numpy as np\n"
                "from scipy import stats\n\n"
                "# Sample size calculation\n"
                "d = 10 / 20  # effect size\n"
                "alpha = 0.05\n"
                "power = 0.80\n"
                "n = (2 * ((stats.norm.ppf(1 - alpha/2) + "
                "stats.norm.ppf(power)) / d) ** 2)\n"
                "print(f'Sample size: {n:.0f} per group')\n"
                "```"
            ),
            "code": (
                "import numpy as np\n"
                "from scipy import stats\n\n"
                "d = 10 / 20\n"
                "alpha = 0.05\n"
                "power = 0.80\n"
                "n = (2 * ((stats.norm.ppf(1 - alpha/2) + "
                "stats.norm.ppf(power)) / d) ** 2)\n"
                "print(f'Sample size: {n:.0f} per group')\n"
            ),
        },
    ],
    "E02": [
        {
            "turn": 1,
            "text": (
                "I need more details about your study. What specific condition "
                "and treatment are you investigating?"
            ),
            "code": "",
        },
        {
            "turn": 2,
            "text": (
                "For a study on SGLT2 inhibitors versus placebo in type 2 "
                "diabetes patients measuring HbA1c, you should design a "
                "randomized controlled trial. Ensure proper randomization, "
                "blinding, and adequate follow-up. Calculate sample size based "
                "on the expected difference in HbA1c."
            ),
            "code": "",
        },
    ],
}


def _build_collected_responses(
    synthetic: dict[str, list[dict]],
    system_id: str,
    cases: dict[str, TestCase],
) -> list[CollectedResponse]:
    """Convert synthetic response dicts into CollectedResponse objects."""
    responses: list[CollectedResponse] = []
    for case_id, turns in synthetic.items():
        case = cases.get(case_id)
        if not case:
            continue
        for turn_data in turns:
            responses.append(
                CollectedResponse(
                    case_id=case_id,
                    system_id=system_id,
                    session_id=f"smoke-{case_id}-{system_id}",
                    turn_number=turn_data["turn"],
                    prompt=(
                        case.prompt if turn_data["turn"] == 1
                        else (
                            case.follow_up_prompts[turn_data["turn"] - 2]
                            if turn_data["turn"] - 2 < len(case.follow_up_prompts)
                            else ""
                        )
                    ),
                    response_text=turn_data["text"],
                    code_output=turn_data.get("code", ""),
                    execution_result="",
                    phase_transitions=(),
                    latency_ms=1500.0,
                    expertise_mode=case.expertise_mode,
                )
            )
    return responses


def _load_smoke_cases() -> dict[str, TestCase]:
    """Load only the test cases needed for the smoke test."""
    base = Path(__file__).parent / "test_cases"
    all_cases: dict[str, TestCase] = {}

    for filename in ("methodology_cases.json", "biostatistics_cases.json", "edge_cases.json"):
        filepath = base / filename
        if not filepath.exists():
            continue
        raw = json.loads(filepath.read_text())
        items = raw if isinstance(raw, list) else raw.get("cases", [])
        for item in items:
            tc = TestCase.model_validate(item)
            if tc.case_id in SMOKE_CASE_IDS:
                all_cases[tc.case_id] = tc

    return all_cases


def _print_header(title: str) -> None:
    width = 60
    print(f"\n{'=' * width}")
    print(f"  {title}")
    print(f"{'=' * width}")


def _print_section(title: str) -> None:
    print(f"\n--- {title} ---")


def run_smoke_auto_eval(config: EvalConfig) -> dict:
    """Run automated evaluation on the synthetic responses."""
    cases_map = _load_smoke_cases()
    chatbot_responses = load_responses("chatbot", config)
    gpt5_responses = load_responses("gpt5", config)

    results = {
        "test_checks": [],
        "completeness_checks": [],
        "code_validations": [],
    }

    for system_id, responses in [("chatbot", chatbot_responses), ("gpt5", gpt5_responses)]:
        by_case = get_responses_by_case(responses)

        for case_id, case_responses in by_case.items():
            case = cases_map.get(case_id)
            if not case:
                continue

            # Use first turn for primary checks
            primary = case_responses[0]
            additional_texts = [r.response_text for r in case_responses[1:]]

            # Test checker (biostatistics only)
            if case.biostatistics_ground_truth:
                gt = case.biostatistics_ground_truth
                tc_result = check_statistical_test(
                    case_id=case_id,
                    system_id=system_id,
                    response_text=primary.response_text,
                    expected_test=gt.correct_statistical_test,
                    accepted_synonyms=gt.test_synonyms,
                )
                results["test_checks"].append({
                    "case_id": case_id,
                    "system_id": system_id,
                    "is_correct": tc_result.is_correct,
                    "expected": tc_result.expected_test,
                    "detected": tc_result.detected_test,
                    "confidence": round(tc_result.confidence, 2),
                })

            # Completeness checker (all cases, multi-turn aware)
            comp = check_completeness(
                case_id=case_id,
                system_id=system_id,
                response_text=primary.response_text,
                additional_response_texts=additional_texts,
            )
            results["completeness_checks"].append({
                "case_id": case_id,
                "system_id": system_id,
                "pico_completeness": round(comp.pico_completeness, 2),
                "bias_count": comp.bias_count,
                "mentions_equator": comp.mentions_equator,
                "has_code_block": comp.has_code_block,
                "word_count": comp.total_word_count,
            })

            # Code validation (if any turn has code)
            code_turns = [r for r in case_responses if r.code_output]
            if code_turns and case.biostatistics_ground_truth:
                gt = case.biostatistics_ground_truth
                code_result = validate_code(
                    case_id=case_id,
                    system_id=system_id,
                    code=code_turns[-1].code_output,
                    expected_pattern=gt.expected_code_output_pattern,
                    timeout_seconds=config.code_execution_timeout_seconds,
                )
                results["code_validations"].append({
                    "case_id": case_id,
                    "system_id": system_id,
                    "syntax_valid": code_result.syntax_valid,
                    "executes": code_result.execution_success,
                    "output": code_result.output_text[:100],
                    "output_matches": code_result.ground_truth_match,
                    "error": code_result.error_text[:100] if code_result.error_text else "",
                })

    return results


def run_smoke_blinding(config: EvalConfig) -> list:
    """Run the blinding step and return blinded pairs."""
    chatbot_responses = load_responses("chatbot", config)
    gpt5_responses = load_responses("gpt5", config)

    chatbot_by_case = get_responses_by_case(chatbot_responses)
    gpt5_by_case = get_responses_by_case(gpt5_responses)

    pairs = create_blinded_pairs(
        chatbot_by_case, gpt5_by_case, seed=config.random_seed
    )
    return pairs


async def run_smoke_judge(pairs: list, config: EvalConfig) -> list:
    """Run the LLM judge on blinded pairs (requires API key)."""
    from evaluation.llm_judge.judge_runner import run_full_evaluation
    from evaluation.rubrics.methodology_rubric import METHODOLOGY_RUBRIC
    from evaluation.rubrics.biostatistics_rubric import BIOSTATISTICS_RUBRIC

    cases_map = _load_smoke_cases()
    cases_list = list(cases_map.values())

    all_results = []

    # Methodology + edge cases
    meth_pairs = [p for p in pairs if p.case_id in ("M01", "E02")]
    if meth_pairs:
        logger.info("Judging %d methodology/edge cases...", len(meth_pairs))
        meth_cases = [c for c in cases_list if c.case_id in ("M01", "E02")]
        results = await run_full_evaluation(
            meth_pairs, meth_cases, METHODOLOGY_RUBRIC, config
        )
        all_results.extend(results)

    # Biostatistics cases
    bio_pairs = [p for p in pairs if p.case_id == "B01"]
    if bio_pairs:
        logger.info("Judging %d biostatistics cases...", len(bio_pairs))
        bio_cases = [c for c in cases_list if c.case_id == "B01"]
        results = await run_full_evaluation(
            bio_pairs, bio_cases, BIOSTATISTICS_RUBRIC, config
        )
        all_results.extend(results)

    return all_results


def main() -> None:
    parser = argparse.ArgumentParser(description="Smoke test for evaluation pipeline")
    parser.add_argument(
        "--with-judge", action="store_true",
        help="Also run the LLM judge (requires ANTHROPIC_API_KEY)",
    )
    parser.add_argument(
        "--judge-runs", type=int, default=1,
        help="Number of judge runs per case (default: 1 for smoke test)",
    )
    args = parser.parse_args()

    _print_header("EVALUATION FRAMEWORK SMOKE TEST")

    # Use a temp directory so we don't pollute the real output
    with tempfile.TemporaryDirectory(prefix="eval_smoke_") as tmpdir:
        config = EvalConfig(
            output_dir=f"{tmpdir}/output",
            raw_responses_dir=f"{tmpdir}/output/raw_responses",
            judge_results_dir=f"{tmpdir}/output/judge_results",
            analysis_dir=f"{tmpdir}/output/analysis",
            reports_dir=f"{tmpdir}/output/reports",
            judge_runs_per_case=args.judge_runs,
        )

        # Step 1: Load test cases
        _print_section("Step 1: Loading test cases")
        cases_map = _load_smoke_cases()
        loaded_ids = sorted(cases_map.keys())
        print(f"  Loaded {len(cases_map)} cases: {loaded_ids}")
        missing = set(SMOKE_CASE_IDS) - set(loaded_ids)
        if missing:
            print(f"  WARNING: Missing cases: {sorted(missing)}")
            sys.exit(1)

        # Step 2: Generate and save synthetic responses
        _print_section("Step 2: Generating synthetic responses")
        chatbot_responses = _build_collected_responses(
            SYNTHETIC_CHATBOT_RESPONSES, "chatbot", cases_map
        )
        gpt5_responses = _build_collected_responses(
            SYNTHETIC_GPT5_RESPONSES, "gpt5", cases_map
        )
        chatbot_path = save_responses(chatbot_responses, "chatbot", config)
        gpt5_path = save_responses(gpt5_responses, "gpt5", config)
        print(f"  Chatbot: {len(chatbot_responses)} responses saved")
        print(f"  GPT-5:   {len(gpt5_responses)} responses saved")

        # Step 3: Run automated evaluation
        _print_section("Step 3: Running automated evaluation")
        auto_results = run_smoke_auto_eval(config)

        print("\n  [Test Checker Results]")
        for tc in auto_results["test_checks"]:
            status = "PASS" if tc["is_correct"] else "FAIL"
            print(f"    {tc['case_id']} ({tc['system_id']}): {status} "
                  f"- detected '{tc['detected']}' "
                  f"(expected '{tc['expected']}', conf={tc['confidence']})")

        print("\n  [Completeness Results]")
        for cc in auto_results["completeness_checks"]:
            print(f"    {cc['case_id']} ({cc['system_id']}): "
                  f"PICO={cc['pico_completeness']:.0%}, "
                  f"biases={cc['bias_count']}, "
                  f"EQUATOR={'yes' if cc['mentions_equator'] else 'no'}, "
                  f"code={'yes' if cc['has_code_block'] else 'no'}, "
                  f"words={cc['word_count']}")

        print("\n  [Code Validation Results]")
        if auto_results["code_validations"]:
            for cv in auto_results["code_validations"]:
                syntax = "valid" if cv["syntax_valid"] else "invalid"
                executes = "runs" if cv["executes"] else "fails"
                matches = "matches" if cv["output_matches"] else "no match"
                print(f"    {cv['case_id']} ({cv['system_id']}): "
                      f"syntax={syntax}, {executes}, output {matches}")
                if cv.get("output"):
                    print(f"      output: {cv['output']}")
                if cv.get("error"):
                    print(f"      error:  {cv['error']}")
        else:
            print("    (no code to validate)")

        # Step 4: Run blinding
        _print_section("Step 4: Creating blinded pairs")
        pairs = run_smoke_blinding(config)
        print(f"  Created {len(pairs)} blinded pairs")
        for p in pairs:
            print(f"    {p.case_id}: system_a={p.label_to_identity['system_a']}, "
                  f"system_b={p.label_to_identity['system_b']}")

        # Step 5: Optionally run judge
        if args.with_judge:
            if not config.anthropic_api_key:
                print("\n  ERROR: --with-judge requires ANTHROPIC_API_KEY")
                print("  Set it via: export ANTHROPIC_API_KEY=sk-ant-...")
                sys.exit(1)

            _print_section(f"Step 5: Running LLM judge ({args.judge_runs} run(s) per case)")
            judge_results = asyncio.run(run_smoke_judge(pairs, config))
            print(f"  Completed {len(judge_results)} evaluations")

            for result in judge_results:
                dim_scores = ", ".join(
                    f"{ds.dimension_id}={ds.score}"
                    for ds in result.dimension_scores
                )
                print(f"    {result.case_id} [{result.system_id}] run={result.judge_run}: "
                      f"overall={result.overall_quality}, "
                      f"composite={result.composite_score:.1f}")
                print(f"      dimensions: {dim_scores}")
        else:
            _print_section("Step 5: LLM judge (skipped)")
            print("  Run with --with-judge to include LLM judge evaluation")
            print("  Requires: export ANTHROPIC_API_KEY=sk-ant-...")

        # Summary
        _print_header("SMOKE TEST SUMMARY")

        total_checks = (
            len(auto_results["test_checks"])
            + len(auto_results["completeness_checks"])
            + len(auto_results["code_validations"])
        )
        test_passes = sum(1 for t in auto_results["test_checks"] if t["is_correct"])
        test_total = len(auto_results["test_checks"])

        print(f"  Cases tested:        {len(cases_map)}")
        print(f"  Responses generated: {len(chatbot_responses) + len(gpt5_responses)}")
        print(f"  Auto-eval checks:    {total_checks}")
        print(f"  Test correctness:    {test_passes}/{test_total}")
        print(f"  Blinded pairs:       {len(pairs)}")
        if args.with_judge:
            print(f"  Judge evaluations:   {len(judge_results)}")
        print(f"\n  All pipeline stages completed successfully.")


if __name__ == "__main__":
    main()
