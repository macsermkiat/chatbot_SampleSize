"""Generate a brief consultation summary from message logs."""

from __future__ import annotations

import logging

from openai import AsyncOpenAI

from app.config import settings

_logger = logging.getLogger(__name__)

SUMMARY_SYSTEM_PROMPT = """\
You are a medical research consultation summarizer. Given a conversation between \
a researcher and an AI research assistant, produce a concise summary (2-3 paragraphs, \
under 1 page) suitable for a human biostatistician or epidemiologist to review \
before a consultation.

Include:
- The research question or topic discussed
- Key methodology decisions or recommendations made
- Statistical considerations (study design, sample size, tests discussed)
- Any unresolved questions or areas needing human expert input

Write in a professional, clinical tone. Do not include greetings or pleasantries. \
Focus on actionable information the reviewing expert needs to know."""


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

    # Use GPT-5-nano for cost-effective summarization
    client = AsyncOpenAI(api_key=settings.openai_api_key)

    try:
        response = await client.chat.completions.create(
            model="gpt-5-nano",
            messages=[
                {"role": "system", "content": SUMMARY_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": f"Summarize this research consultation:\n\n{transcript}",
                },
            ],
            max_tokens=1000,
            temperature=0.3,
        )
        return response.choices[0].message.content or "Summary generation failed."
    except Exception as exc:
        _logger.exception("Failed to generate summary")
        raise RuntimeError(f"Summary generation failed: {exc}") from exc
