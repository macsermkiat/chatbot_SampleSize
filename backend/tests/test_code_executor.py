"""Tests for OpenAI Code Interpreter executor with mocked API."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.code_executor import ExecutionResult, execute_python


# ---------------------------------------------------------------------------
# Helpers to build mock OpenAI objects
# ---------------------------------------------------------------------------

def _make_text_block(text: str) -> MagicMock:
    block = MagicMock()
    block.type = "text"
    block.text = MagicMock(value=text)
    return block


def _make_message(role: str, text: str) -> MagicMock:
    msg = MagicMock()
    msg.role = role
    msg.content = [_make_text_block(text)]
    return msg


def _make_run(status: str, last_error: MagicMock | None = None) -> MagicMock:
    run = MagicMock()
    run.status = status
    run.id = "run_123"
    run.last_error = last_error
    return run


def _build_mock_client(
    run_statuses: list[str],
    messages: list[MagicMock] | None = None,
    last_error: MagicMock | None = None,
) -> MagicMock:
    """Build a mock AsyncOpenAI client that returns runs with given statuses."""
    client = MagicMock()

    # Assistant creation
    assistant = MagicMock(id="asst_test")
    client.beta.assistants.create = AsyncMock(return_value=assistant)

    # Thread creation
    thread = MagicMock(id="thread_test")
    client.beta.threads.create = AsyncMock(return_value=thread)
    client.beta.threads.messages.create = AsyncMock()

    # Run creation -- first status
    initial_run = _make_run(run_statuses[0], last_error)
    client.beta.threads.runs.create = AsyncMock(return_value=initial_run)

    # Run polling -- subsequent statuses
    poll_runs = [_make_run(s, last_error) for s in run_statuses[1:]]
    client.beta.threads.runs.retrieve = AsyncMock(side_effect=poll_runs)

    # Messages list
    msg_list = MagicMock()
    msg_list.data = messages or []
    client.beta.threads.messages.list = AsyncMock(return_value=msg_list)

    # Thread cleanup
    client.beta.threads.delete = AsyncMock()

    return client


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestExecutePython:
    @pytest.fixture(autouse=True)
    def _reset_assistant_id(self):
        """Reset the cached assistant ID between tests."""
        import app.services.code_executor as mod
        original = mod._ASSISTANT_ID
        mod._ASSISTANT_ID = None
        yield
        mod._ASSISTANT_ID = original

    async def test_success(self):
        messages = [_make_message("assistant", "Result: 128 per group")]
        client = _build_mock_client(
            run_statuses=["completed"],
            messages=messages,
        )

        with (
            patch("app.services.code_executor.settings", MagicMock(openai_api_key="sk-test")),
            patch("app.services.code_executor.AsyncOpenAI", return_value=client),
        ):
            result = await execute_python("print('hello')")

        assert result.success is True
        assert "128 per group" in result.stdout
        assert result.error_message == ""

    async def test_polling_until_complete(self):
        messages = [_make_message("assistant", "42")]
        client = _build_mock_client(
            run_statuses=["in_progress", "in_progress", "completed"],
            messages=messages,
        )

        with (
            patch("app.services.code_executor.settings", MagicMock(openai_api_key="sk-test")),
            patch("app.services.code_executor.AsyncOpenAI", return_value=client),
            patch("app.services.code_executor.asyncio.sleep", new_callable=AsyncMock),
        ):
            result = await execute_python("print(42)")

        assert result.success is True
        assert "42" in result.stdout

    async def test_timeout(self):
        # Run stays in_progress forever -- should hit timeout
        client = _build_mock_client(run_statuses=["in_progress"])
        # Make retrieve always return in_progress
        client.beta.threads.runs.retrieve = AsyncMock(
            return_value=_make_run("in_progress"),
        )
        # Also mock thread deletion for cleanup
        client.beta.threads.delete = AsyncMock()

        # Advance monotonic time to exceed timeout
        time_values = iter([0, 0, 3])  # start, first check passes, second check exceeds timeout=2

        with (
            patch("app.services.code_executor.settings", MagicMock(openai_api_key="sk-test")),
            patch("app.services.code_executor.AsyncOpenAI", return_value=client),
            patch("app.services.code_executor.asyncio.sleep", new_callable=AsyncMock),
            patch("app.services.code_executor.time.monotonic", side_effect=time_values),
        ):
            result = await execute_python("while True: pass", timeout=2)

        assert result.success is False
        assert "timed out" in result.error_message

    async def test_runtime_error(self):
        error = MagicMock(message="NameError: name 'x' is not defined")
        client = _build_mock_client(
            run_statuses=["failed"],
            last_error=error,
        )

        with (
            patch("app.services.code_executor.settings", MagicMock(openai_api_key="sk-test")),
            patch("app.services.code_executor.AsyncOpenAI", return_value=client),
        ):
            result = await execute_python("print(x)")

        assert result.success is False
        assert "NameError" in result.error_message

    async def test_missing_api_key(self):
        with patch("app.services.code_executor.settings", MagicMock(openai_api_key="")):
            result = await execute_python("print('hi')")

        assert result.success is False
        assert "API key not configured" in result.error_message

    async def test_unexpected_exception(self):
        with (
            patch("app.services.code_executor.settings", MagicMock(openai_api_key="sk-test")),
            patch(
                "app.services.code_executor.AsyncOpenAI",
                side_effect=RuntimeError("connection failed"),
            ),
        ):
            result = await execute_python("print('hi')")

        assert result.success is False
        assert "internal error" in result.error_message.lower()
