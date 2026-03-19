"""Execute Python code via OpenAI Assistants API (Code Interpreter).

Single responsibility: run a Python script in a sandboxed environment
and return the textual output.
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass

from openai import AsyncOpenAI

from app.config import settings

_logger = logging.getLogger(__name__)

_ASSISTANT_ID: str | None = None
_ASSISTANT_LOCK = asyncio.Lock()


@dataclass(frozen=True)
class ExecutionResult:
    """Immutable result of a code execution."""

    success: bool
    stdout: str
    error_message: str


async def _get_or_create_assistant(client: AsyncOpenAI) -> str:
    """Lazy-create a code-interpreter assistant, caching the ID in-process."""
    global _ASSISTANT_ID  # noqa: PLW0603

    async with _ASSISTANT_LOCK:
        if _ASSISTANT_ID is not None:
            return _ASSISTANT_ID

        assistant = await client.beta.assistants.create(
            name="Biostats Code Runner",
            instructions="Execute the provided Python script and return the printed output verbatim.",
            model="gpt-5.4-mini",
            tools=[{"type": "code_interpreter"}],
        )
        _ASSISTANT_ID = assistant.id
        return _ASSISTANT_ID


async def execute_python(script: str, timeout: int = 300) -> ExecutionResult:
    """Run *script* in a sandboxed Code Interpreter and return output.

    Returns an ``ExecutionResult`` -- never raises.
    """
    if not settings.openai_api_key:
        return ExecutionResult(
            success=False,
            stdout="",
            error_message="OpenAI API key not configured -- cannot execute code.",
        )

    thread_id: str | None = None
    client: AsyncOpenAI | None = None

    try:
        client = AsyncOpenAI(api_key=settings.openai_api_key)
        assistant_id = await _get_or_create_assistant(client)

        thread = await client.beta.threads.create()
        thread_id = thread.id
        await client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=f"Run this Python script and return only the printed output:\n\n```python\n{script}\n```",
        )

        run = await client.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=assistant_id,
        )

        # Poll for completion with wall-clock timeout
        start = time.monotonic()
        poll_interval = 2
        while run.status in ("queued", "in_progress"):
            if time.monotonic() - start >= timeout:
                return ExecutionResult(
                    success=False,
                    stdout="",
                    error_message=f"Code execution timed out after {timeout}s.",
                )
            await asyncio.sleep(poll_interval)
            run = await client.beta.threads.runs.retrieve(
                thread_id=thread_id,
                run_id=run.id,
            )

        if run.status == "failed":
            error_msg = getattr(run.last_error, "message", "Unknown execution error")
            return ExecutionResult(success=False, stdout="", error_message=error_msg)

        # Extract text from assistant messages
        messages = await client.beta.threads.messages.list(thread_id=thread_id)
        output_parts: list[str] = []
        for msg in messages.data:
            if msg.role == "assistant":
                for block in msg.content:
                    if block.type == "text":
                        output_parts.append(block.text.value)

        stdout = "\n".join(output_parts).strip()
        return ExecutionResult(success=True, stdout=stdout, error_message="")

    except Exception as exc:
        _logger.exception("Code execution failed: %s", exc)
        return ExecutionResult(
            success=False,
            stdout="",
            error_message="An internal error occurred during code execution.",
        )

    finally:
        # Clean up the thread to avoid resource leaks
        if thread_id is not None and client is not None:
            try:
                await client.beta.threads.delete(thread_id)
            except Exception:
                _logger.debug("Failed to delete thread %s", thread_id, exc_info=True)
