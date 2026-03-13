"""Generate a brief consultation summary from message logs."""

from __future__ import annotations

import logging

from openai import AsyncOpenAI

from app.config import settings

_logger = logging.getLogger(__name__)

SUMMARY_SYSTEM_PROMPT = """\
Summarize this medical research consultation in 2-3 paragraphs for a biostatistician \
or epidemiologist to review. Include: research question, methodology discussed, \
statistical considerations, and unresolved questions. Professional tone, no greetings."""


async def generate_summary(messages: list[dict]) -> str:
    """Generate a brief summary from conversation messages.

    Args:
        messages: List of dicts with 'role' and 'content' keys.

    Returns:
        Summary text string.
    """
    if not messages:
        return "No conversation messages found for this session."

    # Build conversation transcript for the LLM
    transcript_parts = []
    for msg in messages:
        role_label = msg["role"].capitalize()
        transcript_parts.append(f"{role_label}: {msg['content']}")
    transcript = "\n\n".join(transcript_parts)

    # Use GPT-5-mini for summarization (nano is too constrained for this task)
    client = AsyncOpenAI(api_key=settings.openai_api_key)

    try:
        response = await client.chat.completions.create(
            model="gpt-5-mini",
            messages=[
                {"role": "system", "content": SUMMARY_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": f"Summarize this research consultation:\n\n{transcript}",
                },
            ],
            max_completion_tokens=4000,
        )
        content = (response.choices[0].message.content or "").strip()
        if not content:
            _logger.warning(
                "Summary returned empty content, finish_reason=%s",
                response.choices[0].finish_reason,
            )
            raise RuntimeError("Summary generation returned empty response")
        return content
    except Exception as exc:
        _logger.exception("Failed to generate summary")
        raise RuntimeError(f"Summary generation failed: {exc}") from exc
