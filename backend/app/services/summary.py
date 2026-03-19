"""Generate a comprehensive consultation summary from message logs."""

from __future__ import annotations

import logging

from openai import AsyncOpenAI

from app.config import settings

_logger = logging.getLogger(__name__)

SUMMARY_SYSTEM_PROMPT = """\
You are a medical research writing assistant. Produce a comprehensive consultation \
summary in standard research proposal / manuscript format. Expand as needed -- do NOT \
limit yourself to one page. Accuracy and correct attribution of references are paramount.

FORMAT (use these exact section headings):

## Background and Rationale
Describe the clinical context, knowledge gaps, and why this research is needed. \
Cite every factual claim with an inline numbered reference, e.g. [1], [2].

## Research Question
State the primary research question (PICO/PICOTS format if discussed).

## Study Design and Methodology
Cover study type, target trial emulation details, DAG / confounding analysis, \
bias mitigation, and applicable reporting guidelines (EQUATOR). Cite sources.

## Statistical Analysis Plan
Detail the proposed statistical methods, primary/secondary outcomes, sample size / \
power calculation parameters, effect sizes, assumptions, and any sensitivity analyses. \
Cite statistical references where applicable.

## Unresolved Issues and Recommendations
List open questions, items requiring further clarification, and next steps.

## References
List ALL references cited in the text above using Vancouver style. Number them in \
order of first appearance. Include author(s), title, journal/source, year, and URL \
or DOI when available. Every reference number in the text MUST appear in this list \
and vice versa. Double-check that each inline citation [N] matches the correct entry.

---

## Executive Summary (1-page)
After the full report above, add a concise 1-page executive summary (2-3 paragraphs) \
covering: research question, methodology, key statistical considerations, and \
unresolved questions. This section is for quick review by a biostatistician or \
epidemiologist. Professional tone, no greetings.

IMPORTANT RULES:
- Accuracy is the highest priority. Only state facts that are supported by the \
conversation. Do not fabricate references or data.
- Every factual statement that originates from a cited source in the conversation \
MUST carry the correct inline reference number.
- If the conversation did not discuss a section, write "Not discussed in this \
consultation." rather than inventing content.
- Professional, formal academic tone throughout."""


async def generate_summary(messages: list[dict]) -> str:
    """Generate a comprehensive manuscript-format summary from conversation messages.

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
    # Set a 25-second timeout so it completes within Vercel's proxy window
    client = AsyncOpenAI(api_key=settings.openai_api_key, timeout=25.0)

    try:
        response = await client.chat.completions.create(
            model="gpt-5-mini",
            messages=[
                {"role": "system", "content": SUMMARY_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": (
                        "Produce a comprehensive research consultation summary "
                        "from the following transcript. Ensure every inline "
                        "reference [N] maps to the correct entry in the "
                        "References section.\n\n"
                        f"{transcript}"
                    ),
                },
            ],
            max_completion_tokens=16000,
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
