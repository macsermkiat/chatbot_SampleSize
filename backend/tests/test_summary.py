"""Tests for summary generation service."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.summary import generate_summary


class TestGenerateSummary:
    """Tests for the generate_summary function."""

    async def test_empty_messages_returns_no_messages_text(self):
        result = await generate_summary([])
        assert result == "No conversation messages found for this session."

    async def test_calls_openai_with_correct_model(self):
        messages = [
            {"role": "user", "content": "What sample size do I need?"},
            {"role": "assistant", "content": "For a two-arm RCT, you need..."},
        ]

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Summary of consultation."

        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        with patch("app.services.summary.AsyncOpenAI", return_value=mock_client):
            result = await generate_summary(messages)

        assert result == "Summary of consultation."

        # Verify the call used gpt-5-nano
        call_kwargs = mock_client.chat.completions.create.call_args
        assert call_kwargs.kwargs["model"] == "gpt-5-nano"
        assert call_kwargs.kwargs["temperature"] == 0.3
        assert call_kwargs.kwargs["max_tokens"] == 1000

    async def test_includes_all_messages_in_transcript(self):
        messages = [
            {"role": "user", "content": "First question"},
            {"role": "assistant", "content": "First answer"},
            {"role": "user", "content": "Second question"},
        ]

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Summary."

        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        with patch("app.services.summary.AsyncOpenAI", return_value=mock_client):
            await generate_summary(messages)

        call_kwargs = mock_client.chat.completions.create.call_args
        user_message = call_kwargs.kwargs["messages"][1]["content"]
        assert "First question" in user_message
        assert "First answer" in user_message
        assert "Second question" in user_message

    async def test_system_prompt_mentions_biostatistician(self):
        messages = [{"role": "user", "content": "Test"}]

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Summary."

        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        with patch("app.services.summary.AsyncOpenAI", return_value=mock_client):
            await generate_summary(messages)

        call_kwargs = mock_client.chat.completions.create.call_args
        system_msg = call_kwargs.kwargs["messages"][0]["content"]
        assert "biostatistician" in system_msg
        assert "epidemiologist" in system_msg

    async def test_raises_runtime_error_on_api_failure(self):
        messages = [{"role": "user", "content": "Test"}]

        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(
            side_effect=Exception("API rate limit"),
        )

        with patch("app.services.summary.AsyncOpenAI", return_value=mock_client):
            with pytest.raises(RuntimeError, match="Summary generation failed"):
                await generate_summary(messages)

    async def test_handles_none_content_response(self):
        messages = [{"role": "user", "content": "Test"}]

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = None

        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        with patch("app.services.summary.AsyncOpenAI", return_value=mock_client):
            result = await generate_summary(messages)

        assert result == "Summary generation failed."
