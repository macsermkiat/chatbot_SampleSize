"""Citation extraction service -- extracts markdown links from messages and builds bibliography."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime

from app.data.reference_registry import StaticReference, find_matching_references


@dataclass(frozen=True)
class Citation:
    """An immutable citation entry."""

    number: int
    title: str
    url: str
    source_phase: str
    is_static: bool
    static_ref: StaticReference | None = None


_MD_LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")


def _normalize_url(url: str) -> str:
    """Normalize a URL for deduplication: strip trailing slash and fragment."""
    url = url.split("#")[0]
    return url.rstrip("/")


def extract_citations_from_messages(
    messages: list[dict[str, str]],
) -> list[Citation]:
    """Extract markdown-link citations from assistant messages.

    Returns deduplicated citations in first-occurrence order, merged with
    matching static references from the reference registry.
    """
    seen_urls: dict[str, int] = {}
    citations: list[Citation] = []
    counter = 0

    # Pass 1: extract inline markdown links from assistant messages
    for msg in messages:
        if msg.get("role") != "assistant":
            continue
        content = msg.get("content", "")
        phase = msg.get("phase", "")

        for match in _MD_LINK_RE.finditer(content):
            title = match.group(1)
            raw_url = match.group(2)
            norm = _normalize_url(raw_url)

            if norm in seen_urls:
                continue

            counter += 1
            seen_urls[norm] = counter
            citations.append(Citation(
                number=counter,
                title=title,
                url=raw_url,
                source_phase=phase,
                is_static=False,
            ))

    # Pass 2: merge static references matched by keyword in all assistant text
    full_text = " ".join(
        msg.get("content", "")
        for msg in messages
        if msg.get("role") == "assistant"
    )
    matched_refs = find_matching_references(full_text)

    for ref in matched_refs:
        norm = _normalize_url(ref.url)
        if norm in seen_urls:
            continue

        counter += 1
        seen_urls[norm] = counter
        citations.append(Citation(
            number=counter,
            title=ref.title,
            url=ref.url,
            source_phase="",
            is_static=True,
            static_ref=ref,
        ))

    return citations


def format_vancouver_bibliography(citations: list[Citation]) -> str:
    """Format citations as a Vancouver-style numbered bibliography string."""
    if not citations:
        return ""

    today = datetime.now().strftime("%d %B %Y")
    lines: list[str] = []

    for c in citations:
        if c.is_static and c.static_ref is not None:
            ref = c.static_ref
            lines.append(
                f"{c.number}. {ref.authors}. {ref.title}. "
                f"{ref.source}. {ref.year}. Available from: {ref.url}"
            )
        else:
            lines.append(
                f"{c.number}. {c.title}. Available from: {c.url}. "
                f"Accessed {today}."
            )

    return "\n".join(lines)
