"""Validate code extracted from responses by executing it and checking output."""

from __future__ import annotations

import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass


@dataclass(frozen=True)
class CodeValidationResult:
    """Result of validating code from a response."""

    case_id: str
    system_id: str
    code_extracted: bool
    syntax_valid: bool
    execution_success: bool
    output_text: str
    error_text: str
    ground_truth_match: bool
    tolerance_pct: float
    execution_time_ms: float


def validate_code(
    case_id: str,
    system_id: str,
    code: str,
    expected_pattern: str = "",
    timeout_seconds: int = 30,
) -> CodeValidationResult:
    """Execute code in a subprocess and validate the output.

    Args:
        case_id: The test case identifier.
        system_id: Which system produced the code ('chatbot' or 'gpt5').
        code: The Python code to execute.
        expected_pattern: Regex pattern to match in stdout.
        timeout_seconds: Max execution time.

    Returns:
        CodeValidationResult with all validation details.
    """
    if not code.strip():
        return CodeValidationResult(
            case_id=case_id,
            system_id=system_id,
            code_extracted=False,
            syntax_valid=False,
            execution_success=False,
            output_text="",
            error_text="No code extracted",
            ground_truth_match=False,
            tolerance_pct=0.0,
            execution_time_ms=0.0,
        )

    # Check syntax
    syntax_valid = _check_syntax(code)
    if not syntax_valid:
        return CodeValidationResult(
            case_id=case_id,
            system_id=system_id,
            code_extracted=True,
            syntax_valid=False,
            execution_success=False,
            output_text="",
            error_text="Syntax error",
            ground_truth_match=False,
            tolerance_pct=0.0,
            execution_time_ms=0.0,
        )

    # Execute code
    output_text, error_text, execution_time_ms, success = _execute_code(
        code, timeout_seconds
    )

    # Check ground truth match
    ground_truth_match = False
    tolerance_pct = 0.0
    if success and expected_pattern:
        ground_truth_match = bool(re.search(expected_pattern, output_text))
        # Try to extract numeric values for tolerance calculation
        tolerance_pct = _calculate_tolerance(output_text, expected_pattern)

    return CodeValidationResult(
        case_id=case_id,
        system_id=system_id,
        code_extracted=True,
        syntax_valid=True,
        execution_success=success,
        output_text=output_text[:2000],  # Truncate for storage
        error_text=error_text[:500],
        ground_truth_match=ground_truth_match,
        tolerance_pct=tolerance_pct,
        execution_time_ms=execution_time_ms,
    )


def _check_syntax(code: str) -> bool:
    """Check if code has valid Python syntax."""
    try:
        compile(code, "<eval>", "exec")
        return True
    except SyntaxError:
        return False


def _execute_code(
    code: str, timeout_seconds: int
) -> tuple[str, str, float, bool]:
    """Execute Python code in a sandboxed subprocess.

    Returns (stdout, stderr, elapsed_ms, success).
    """
    # Strip any pip install or subprocess calls for safety
    safe_code = _sanitize_code(code)

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".py", delete=False
    ) as tmp:
        tmp.write(safe_code)
        tmp_path = tmp.name

    import time

    start = time.monotonic()
    try:
        result = subprocess.run(
            [sys.executable, tmp_path],
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
        elapsed_ms = (time.monotonic() - start) * 1000
        return (
            result.stdout,
            result.stderr,
            elapsed_ms,
            result.returncode == 0,
        )
    except subprocess.TimeoutExpired:
        elapsed_ms = (time.monotonic() - start) * 1000
        return ("", f"Timeout after {timeout_seconds}s", elapsed_ms, False)
    except Exception as exc:
        elapsed_ms = (time.monotonic() - start) * 1000
        return ("", str(exc), elapsed_ms, False)


def _sanitize_code(code: str) -> str:
    """Remove potentially dangerous operations from code."""
    lines = code.split("\n")
    safe_lines = []
    for line in lines:
        stripped = line.strip()
        # Skip pip install, subprocess, os.system calls
        if any(
            pattern in stripped
            for pattern in [
                "pip install",
                "subprocess",
                "os.system",
                "os.popen",
                "shutil.rmtree",
                "__import__",
            ]
        ):
            safe_lines.append(f"# REMOVED: {stripped}")
        else:
            safe_lines.append(line)
    return "\n".join(safe_lines)


def _calculate_tolerance(output: str, expected_pattern: str) -> float:
    """Try to extract numeric tolerance between output and expected."""
    # Extract numbers from output
    output_numbers = re.findall(r"[\d]+\.?[\d]*", output)
    expected_numbers = re.findall(r"[\d]+\.?[\d]*", expected_pattern)

    if not output_numbers or not expected_numbers:
        return 0.0

    try:
        actual = float(output_numbers[0])
        expected = float(expected_numbers[0])
        if expected == 0:
            return 0.0
        return abs(actual - expected) / expected * 100
    except (ValueError, IndexError):
        return 0.0
