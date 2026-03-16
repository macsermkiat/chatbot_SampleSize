"""Automated validation runner -- sends benchmarks through the chatbot and scores results.

Usage:
    cd backend
    .venv/bin/python -m evaluation.validators.validation_runner

Requires the backend to be running on localhost:8000.
Results are saved to evaluation/output/validation/.
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import httpx

from evaluation.config import EvalConfig
from evaluation.validators.prompt_generator import generate_prompt
from evaluation.validators.sample_size_extractor import extract_sample_size
from evaluation.validators.sample_size_validator import (
    Benchmark,
    ScoreResult,
    compute_concordance,
    generate_validation_report,
    load_benchmarks,
    score_result,
)

logger = logging.getLogger(__name__)

_OUTPUT_DIR = Path(__file__).parent.parent / "output" / "validation"


@dataclass(frozen=True)
class BenchmarkResult:
    """Result of running a single benchmark through the chatbot."""

    benchmark_id: str
    scenario: str
    prompt: str
    response_text: str
    code_output: str
    execution_result: str
    extracted_n: int | None
    extraction_source: str
    expected_n: int
    score: dict[str, Any]
    latency_ms: float
    error: str


async def _send_benchmark(
    benchmark: Benchmark,
    config: EvalConfig,
) -> BenchmarkResult:
    """Send a single benchmark through the chatbot and extract the result."""
    prompt = generate_prompt(benchmark.id, benchmark.parameters)
    session_id = f"val-{benchmark.id}-{uuid.uuid4().hex[:8]}"

    # Determine expected N
    expected_n = _get_expected_n(benchmark)

    start = time.monotonic()
    try:
        response = await _collect_response(
            prompt=prompt,
            session_id=session_id,
            api_url=config.chatbot_api_url,
            timeout=config.chatbot_timeout_seconds,
        )
    except Exception as exc:
        elapsed = (time.monotonic() - start) * 1000
        return BenchmarkResult(
            benchmark_id=benchmark.id,
            scenario=benchmark.scenario,
            prompt=prompt,
            response_text="",
            code_output="",
            execution_result="",
            extracted_n=None,
            extraction_source="",
            expected_n=expected_n,
            score={},
            latency_ms=elapsed,
            error=str(exc),
        )

    elapsed = (time.monotonic() - start) * 1000

    # Extract sample size from response
    extracted = extract_sample_size(
        response_text=response["text"],
        code_output=response["code"],
        execution_result=response["execution_result"],
        expected_keys=benchmark.expected,
    )

    extracted_n = extracted.value if extracted else None
    extraction_source = extracted.source if extracted else ""

    # Score if we got a value
    score_dict: dict[str, Any] = {}
    if extracted_n is not None:
        sr = score_result(
            actual=extracted_n,
            expected=expected_n,
            tolerance_5pct=benchmark.tolerance_5pct,
            tolerance_10pct=benchmark.tolerance_10pct,
        )
        score_dict = {
            "exact_match": sr.exact_match,
            "within_5pct": sr.within_5pct,
            "within_10pct": sr.within_10pct,
            "deviation_pct": sr.deviation_pct,
        }

    return BenchmarkResult(
        benchmark_id=benchmark.id,
        scenario=benchmark.scenario,
        prompt=prompt,
        response_text=response["text"],
        code_output=response["code"],
        execution_result=response["execution_result"],
        extracted_n=extracted_n,
        extraction_source=extraction_source,
        expected_n=expected_n,
        score=score_dict,
        latency_ms=elapsed,
        error="",
    )


def _get_expected_n(benchmark: Benchmark) -> int:
    """Get the primary expected N from a benchmark."""
    exp = benchmark.expected
    for key in ("n_per_group", "total_n", "total_events", "n_per_group_individual", "n_control"):
        if key in exp:
            return int(exp[key])
    return 0


async def _collect_response(
    prompt: str,
    session_id: str,
    api_url: str,
    timeout: int,
) -> dict[str, str]:
    """Send prompt to chatbot SSE endpoint and collect the response."""
    text_parts: list[str] = []
    code_parts: list[str] = []
    execution_result = ""

    stream_timeout = httpx.Timeout(
        connect=10.0,
        read=float(timeout),
        write=10.0,
        pool=10.0,
    )

    async with httpx.AsyncClient() as client:
        async with client.stream(
            "POST",
            api_url,
            json={
                "message": prompt,
                "session_id": session_id,
                "expertise_level": "advanced",
            },
            timeout=stream_timeout,
            headers={"Accept": "text/event-stream"},
        ) as stream:
            current_event = ""
            async for line in stream.aiter_lines():
                line = line.strip()
                if not line:
                    current_event = ""
                    continue

                if line.startswith("event:"):
                    current_event = line[6:].strip()
                    if current_event == "done":
                        break
                    continue

                if line.startswith("data:"):
                    data_str = line[5:].strip()
                    try:
                        data = json.loads(data_str)
                    except (json.JSONDecodeError, ValueError):
                        continue

                    if current_event in ("message", ""):
                        content = data.get("content", "")
                        if content:
                            text_parts.append(content)
                    elif current_event == "code":
                        script = data.get("script", "")
                        if script:
                            code_parts.append(script)
                    elif current_event == "execution_result":
                        execution_result = data.get("stdout", "")

    return {
        "text": "".join(text_parts),
        "code": "\n".join(code_parts),
        "execution_result": execution_result,
    }


async def run_validation(
    benchmark_ids: list[str] | None = None,
    resume: bool = True,
) -> tuple[list[BenchmarkResult], str]:
    """Run validation against the chatbot for all (or selected) benchmarks.

    Args:
        benchmark_ids: If provided, only run these benchmark IDs. Otherwise all.
        resume: If True, skip benchmarks that already have results on disk.

    Returns:
        Tuple of (results list, report markdown string).
    """
    config = EvalConfig()
    suite = load_benchmarks()

    benchmarks = suite.benchmarks
    if benchmark_ids:
        id_set = set(benchmark_ids)
        benchmarks = [b for b in benchmarks if b.id in id_set]

    # Resume support: load existing results
    completed_ids: set[str] = set()
    existing_results: list[BenchmarkResult] = []
    if resume:
        existing_results = _load_results()
        completed_ids = {r.benchmark_id for r in existing_results if not r.error}

    all_results: list[BenchmarkResult] = list(existing_results) if completed_ids else []

    pending = [b for b in benchmarks if b.id not in completed_ids]
    if not pending:
        logger.info("All %d benchmarks already completed", len(benchmarks))
    else:
        logger.info(
            "Running %d benchmarks (%d already completed)",
            len(pending), len(completed_ids),
        )

    for i, benchmark in enumerate(pending, 1):
        logger.info(
            "[%d/%d] %s: %s", i, len(pending), benchmark.id, benchmark.scenario,
        )
        result = await _send_benchmark(benchmark, config)

        if result.error:
            logger.warning("  ERROR: %s", result.error)
        elif result.extracted_n is None:
            logger.warning("  Could not extract N from response")
        else:
            score = result.score
            logger.info(
                "  Expected=%d, Got=%d (%.1f%% dev) exact=%s 5%%=%s 10%%=%s",
                result.expected_n,
                result.extracted_n,
                score.get("deviation_pct", 0),
                score.get("exact_match", False),
                score.get("within_5pct", False),
                score.get("within_10pct", False),
            )

        all_results.append(result)
        _save_results(all_results)

    # Build score results for the report
    score_results = []
    for r in all_results:
        if r.extracted_n is not None and not r.error:
            sr = ScoreResult(
                benchmark_id=r.benchmark_id,
                actual=r.extracted_n,
                expected=r.expected_n,
                exact_match=r.score.get("exact_match", False),
                within_5pct=r.score.get("within_5pct", False),
                within_10pct=r.score.get("within_10pct", False),
                deviation_pct=r.score.get("deviation_pct", 0.0),
            )
            score_results.append(sr)

    summary = compute_concordance(score_results)
    report = generate_validation_report(score_results, summary)

    # Save report
    _OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    report_path = _OUTPUT_DIR / "validation_report.md"
    report_path.write_text(report)
    logger.info("Report saved to %s", report_path)
    logger.info(
        "Summary: %d/%d exact, %d/%d within 5%%, %d/%d within 10%%",
        summary.exact_match_count, summary.total,
        summary.within_5pct_count, summary.total,
        summary.within_10pct_count, summary.total,
    )

    return all_results, report


def _save_results(results: list[BenchmarkResult]) -> None:
    """Save results to disk for crash resilience."""
    _OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    filepath = _OUTPUT_DIR / "validation_results.json"
    data = [asdict(r) for r in results]
    filepath.write_text(json.dumps(data, indent=2, default=str))


def _load_results() -> list[BenchmarkResult]:
    """Load previously saved results."""
    filepath = _OUTPUT_DIR / "validation_results.json"
    if not filepath.exists():
        return []
    try:
        data = json.loads(filepath.read_text())
        return [
            BenchmarkResult(
                benchmark_id=item["benchmark_id"],
                scenario=item["scenario"],
                prompt=item["prompt"],
                response_text=item["response_text"],
                code_output=item["code_output"],
                execution_result=item.get("execution_result", ""),
                extracted_n=item.get("extracted_n"),
                extraction_source=item.get("extraction_source", ""),
                expected_n=item["expected_n"],
                score=item.get("score", {}),
                latency_ms=item.get("latency_ms", 0),
                error=item.get("error", ""),
            )
            for item in data
        ]
    except (json.JSONDecodeError, KeyError):
        return []


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )
    asyncio.run(run_validation())
