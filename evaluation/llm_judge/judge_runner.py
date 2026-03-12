"""Orchestrate LLM judge evaluations across all cases and dimensions.

Uses batched prompts by default: all dimensions + overall quality are
scored in a single API call per response, reducing cost by ~80-90%
compared to the per-dimension approach.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from anthropic import AsyncAnthropic

from evaluation.config import EvalConfig
from evaluation.llm_judge.blinding import BlindedPair, BlindedResponse
from evaluation.llm_judge.judge_prompt import (
    JUDGE_BATCH_SYSTEM_PROMPT,
    JUDGE_SYSTEM_PROMPT,
    build_batch_evaluation_prompt,
    build_evaluation_prompt,
    build_overall_quality_prompt,
)
from evaluation.rubrics.schema import (
    DimensionScore,
    EvaluationResult,
    Rubric,
)
from evaluation.test_cases.schema import TestCase

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Batched evaluation (default) -- 1 API call per response
# ---------------------------------------------------------------------------

async def evaluate_single_response(
    response: BlindedResponse,
    case: TestCase,
    rubric: Rubric,
    config: EvalConfig,
    judge_run: int,
) -> EvaluationResult:
    """Evaluate a single blinded response across all rubric dimensions.

    Uses a single batched API call that scores all dimensions + overall
    quality at once.
    """
    client = AsyncAnthropic(api_key=config.anthropic_api_key)

    prompt = build_batch_evaluation_prompt(
        rubric=rubric,
        case_context=case.clinical_context,
        user_prompt=case.prompt,
        response_text=response.text,
        expertise_mode=case.expertise_mode,
        agent_type=case.agent_target,
        code_output=response.code,
    )

    result_data = await _call_judge(
        client, prompt, config, system_prompt=JUDGE_BATCH_SYSTEM_PROMPT
    )

    dimension_scores = _parse_batch_dimensions(result_data, rubric)
    overall = result_data.get("overall", {})

    return EvaluationResult(
        case_id=case.case_id,
        system_id=response.blinded_label,
        judge_run=judge_run,
        rubric_id=rubric.rubric_id,
        dimension_scores=dimension_scores,
        overall_quality=_clamp_score(overall.get("score", 3)),
        overall_reasoning=overall.get("reasoning", ""),
    )


def _parse_batch_dimensions(
    result_data: dict, rubric: Rubric
) -> list[DimensionScore]:
    """Parse the dimensions array from a batched judge response."""
    raw_dims = result_data.get("dimensions", [])
    dim_map: dict[str, dict] = {}
    for item in raw_dims:
        dim_id = item.get("dimension_id", "")
        if dim_id:
            dim_map[dim_id] = item

    scores: list[DimensionScore] = []
    for dimension in rubric.dimensions:
        item = dim_map.get(dimension.dimension_id, {})
        scores.append(
            DimensionScore(
                dimension_id=dimension.dimension_id,
                score=_clamp_score(item.get("score", 3)),
                reasoning=item.get("reasoning", ""),
                evidence=item.get("evidence", ""),
            )
        )
    return scores


def _clamp_score(value: int | float | str) -> int:
    """Clamp a score to 1-5 integer range."""
    try:
        score = int(value)
    except (TypeError, ValueError):
        return 3
    return max(1, min(5, score))


# ---------------------------------------------------------------------------
# Per-dimension evaluation (legacy fallback)
# ---------------------------------------------------------------------------

async def evaluate_single_response_per_dimension(
    response: BlindedResponse,
    case: TestCase,
    rubric: Rubric,
    config: EvalConfig,
    judge_run: int,
) -> EvaluationResult:
    """Legacy: evaluate one dimension per API call (9 calls per response)."""
    client = AsyncAnthropic(api_key=config.anthropic_api_key)
    dimension_scores: list[DimensionScore] = []

    for dimension in rubric.dimensions:
        prompt = build_evaluation_prompt(
            dimension=dimension,
            case_context=case.clinical_context,
            user_prompt=case.prompt,
            response_text=response.text,
            expertise_mode=case.expertise_mode,
            code_output=response.code if dimension.dimension_id in ("B3", "B8") else "",
        )

        score_data = await _call_judge(client, prompt, config)

        dimension_scores.append(
            DimensionScore(
                dimension_id=dimension.dimension_id,
                score=_clamp_score(score_data.get("score", 3)),
                reasoning=score_data.get("reasoning", ""),
                evidence=score_data.get("evidence", ""),
            )
        )

    overall_prompt = build_overall_quality_prompt(
        case_context=case.clinical_context,
        user_prompt=case.prompt,
        response_text=response.text,
        expertise_mode=case.expertise_mode,
        agent_type=case.agent_target,
    )
    overall_data = await _call_judge(client, overall_prompt, config)

    return EvaluationResult(
        case_id=case.case_id,
        system_id=response.blinded_label,
        judge_run=judge_run,
        rubric_id=rubric.rubric_id,
        dimension_scores=dimension_scores,
        overall_quality=_clamp_score(overall_data.get("score", 3)),
        overall_reasoning=overall_data.get("reasoning", ""),
    )


# ---------------------------------------------------------------------------
# Pair and full evaluation orchestration
# ---------------------------------------------------------------------------

async def evaluate_blinded_pair(
    pair: BlindedPair,
    case: TestCase,
    rubric: Rubric,
    config: EvalConfig,
) -> list[EvaluationResult]:
    """Evaluate both systems in a blinded pair across all judge runs."""
    results: list[EvaluationResult] = []

    for run in range(1, config.judge_runs_per_case + 1):
        for response in [pair.system_a, pair.system_b]:
            result = await evaluate_single_response(
                response=response,
                case=case,
                rubric=rubric,
                config=config,
                judge_run=run,
            )
            results.append(result)

    return results


async def run_full_evaluation(
    pairs: list[BlindedPair],
    cases: list[TestCase],
    rubric: Rubric,
    config: EvalConfig,
    existing_results: list[EvaluationResult] | None = None,
) -> list[EvaluationResult]:
    """Run the complete evaluation across all pairs.

    Args:
        existing_results: Previously collected results to preserve in
            incremental saves (avoids overwriting results from earlier
            rubric evaluations).
    """
    case_lookup = {c.case_id: c for c in cases}
    new_results: list[EvaluationResult] = []

    for pair in pairs:
        case = case_lookup.get(pair.case_id)
        if not case:
            logger.warning("No test case found for %s", pair.case_id)
            continue

        logger.info("Evaluating case %s...", pair.case_id)
        results = await evaluate_blinded_pair(pair, case, rubric, config)
        new_results.extend(results)

        # Save incremental results (include existing to avoid overwriting)
        combined = list(existing_results or []) + new_results
        _save_results(combined, config)

    return new_results


# ---------------------------------------------------------------------------
# LLM call and persistence
# ---------------------------------------------------------------------------

async def _call_judge(
    client: AsyncAnthropic,
    user_prompt: str,
    config: EvalConfig,
    system_prompt: str = JUDGE_SYSTEM_PROMPT,
) -> dict:
    """Call the LLM judge and parse the JSON response.

    Uses prompt caching on the system prompt to reduce cost on repeated
    calls with the same system prompt (all calls within a rubric type
    share the same system prompt).
    """
    try:
        message = await client.messages.create(
            model=config.judge_model,
            max_tokens=2048,
            temperature=config.judge_temperature,
            system=[
                {
                    "type": "text",
                    "text": system_prompt,
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            messages=[{"role": "user", "content": user_prompt}],
        )

        response_text = message.content[0].text.strip()

        # Try to parse JSON from the response
        # Handle cases where the model wraps in markdown fences
        json_text = response_text
        if "```" in json_text:
            json_text = json_text.split("```")[1]
            if json_text.startswith("json"):
                json_text = json_text[4:]

        return json.loads(json_text)

    except (json.JSONDecodeError, IndexError, KeyError) as exc:
        logger.warning("Failed to parse judge response: %s", exc)
        return {"score": 3, "reasoning": "Parse error", "evidence": ""}
    except Exception as exc:
        logger.error("Judge API call failed: %s", exc)
        return {"score": 3, "reasoning": f"API error: {exc}", "evidence": ""}


def _save_results(results: list[EvaluationResult], config: EvalConfig) -> None:
    """Save results incrementally to disk."""
    output_dir = Path(config.judge_results_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    filepath = output_dir / "judge_results.json"
    data = [r.model_dump() for r in results]
    filepath.write_text(json.dumps(data, indent=2, default=str))
