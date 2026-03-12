"""Re-run methodology judge evaluation and merge with existing bio results.

This script fixes the issue where biostatistics incremental saves
overwrote methodology results during the initial run.

Usage:
    cd chatbot_SampleSize
    set -a && source backend/.env && set +a
    backend/.venv/bin/python -m evaluation.rerun_methodology_judge
"""

from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path

from evaluation.config import EvalConfig
from evaluation.runner import load_test_cases
from evaluation.collectors.response_store import (
    get_responses_by_case,
    load_responses,
)
from evaluation.llm_judge.blinding import create_blinded_pairs
from evaluation.llm_judge.judge_runner import (
    run_full_evaluation,
    _save_results,
)
from evaluation.rubrics.methodology_rubric import METHODOLOGY_RUBRIC
from evaluation.rubrics.schema import EvaluationResult

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


async def main() -> None:
    config = EvalConfig()
    cases = load_test_cases()

    # Load existing bio results from disk
    judge_file = Path(config.judge_results_dir) / "judge_results.json"
    existing_results: list[EvaluationResult] = []
    if judge_file.exists():
        data = json.loads(judge_file.read_text())
        existing_results = [EvaluationResult.model_validate(r) for r in data]
        existing_case_ids = set(r.case_id for r in existing_results)
        logger.info(
            "Loaded %d existing results for %d cases: %s",
            len(existing_results),
            len(existing_case_ids),
            sorted(existing_case_ids),
        )

    # Load responses and create blinded pairs
    chatbot_responses = load_responses("chatbot", config)
    gpt5_responses = load_responses("gpt5", config)
    chatbot_by_case = get_responses_by_case(chatbot_responses)
    gpt5_by_case = get_responses_by_case(gpt5_responses)

    pairs = create_blinded_pairs(
        chatbot_by_case, gpt5_by_case, seed=config.random_seed
    )

    # Filter to methodology + edge cases only
    methodology_cases = [c for c in cases if c.agent_target == "methodology"]
    edge_cases = [c for c in cases if c.case_id.startswith("E")]
    meth_edge_cases = methodology_cases + edge_cases
    meth_case_ids = {c.case_id for c in meth_edge_cases}

    meth_pairs = [p for p in pairs if p.case_id in meth_case_ids]
    logger.info("Running methodology/edge evaluation: %d pairs", len(meth_pairs))

    # Run methodology evaluation with existing bio results preserved
    meth_results = await run_full_evaluation(
        meth_pairs,
        meth_edge_cases,
        METHODOLOGY_RUBRIC,
        config,
        existing_results=existing_results,
    )

    # Save final combined results
    combined = existing_results + meth_results
    _save_results(combined, config)
    logger.info(
        "Saved %d combined results (%d existing + %d methodology)",
        len(combined),
        len(existing_results),
        len(meth_results),
    )


if __name__ == "__main__":
    asyncio.run(main())
