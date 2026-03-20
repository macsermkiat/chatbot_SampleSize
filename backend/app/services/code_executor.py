"""Execute Python code via OpenAI Responses API (Code Interpreter).

Single responsibility: run a Python script in a sandboxed environment
and return the textual output.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from openai import AsyncOpenAI

from app.config import settings

_logger = logging.getLogger(__name__)

_CODE_INTERPRETER_MODEL = "gpt-5.4-mini"


@dataclass(frozen=True)
class ExecutionResult:
    """Immutable result of a code execution."""

    success: bool
    stdout: str
    error_message: str


async def execute_python(script: str, timeout: int = 300) -> ExecutionResult:
    """Run *script* in a sandboxed Code Interpreter and return output.

    Uses the Responses API with the code_interpreter tool.
    Returns an ``ExecutionResult`` -- never raises.
    """
    if not settings.openai_api_key:
        return ExecutionResult(
            success=False,
            stdout="",
            error_message="OpenAI API key not configured -- cannot execute code.",
        )

    try:
        client = AsyncOpenAI(
            api_key=settings.openai_api_key,
            timeout=float(timeout),
        )

        response = await client.responses.create(
            model=_CODE_INTERPRETER_MODEL,
            instructions="Execute the provided Python script and return the printed output verbatim.",
            tools=[
                {
                    "type": "code_interpreter",
                    "container": {"type": "auto"},
                },
            ],
            input=f"Run this Python script and return only the printed output:\n\n```python\n{script}\n```",
        )

        # Extract text output from response
        output_parts: list[str] = []
        for item in response.output:
            if item.type == "message":
                for block in item.content:
                    if block.type == "output_text":
                        output_parts.append(block.text)

        stdout = "\n".join(output_parts).strip()
        return ExecutionResult(success=True, stdout=stdout, error_message="")

    except Exception as exc:
        _logger.exception("Code execution failed: %s", exc)
        return ExecutionResult(
            success=False,
            stdout="",
            error_message=f"Code execution error: {exc}",
        )
