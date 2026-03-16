"""Tests for citation extraction service."""

from __future__ import annotations

import pytest

from app.services.citation_extractor import (
    Citation,
    _normalize_url,
    extract_citations_from_messages,
    format_vancouver_bibliography,
)
from app.data.reference_registry import find_matching_references


# ---------------------------------------------------------------------------
# URL normalisation
# ---------------------------------------------------------------------------

class TestNormalizeUrl:
    def test_strips_trailing_slash(self):
        assert _normalize_url("https://example.com/") == "https://example.com"

    def test_strips_fragment(self):
        assert _normalize_url("https://example.com/page#section") == "https://example.com/page"

    def test_strips_both(self):
        assert _normalize_url("https://example.com/page/#top") == "https://example.com/page"

    def test_no_change_needed(self):
        assert _normalize_url("https://example.com/page") == "https://example.com/page"


# ---------------------------------------------------------------------------
# extract_citations_from_messages
# ---------------------------------------------------------------------------

MESSAGES_WITH_LINKS = [
    {"role": "user", "content": "What about [User Link](https://user.com)?", "phase": ""},
    {
        "role": "assistant",
        "content": "See [Study A](https://example.com/a) and [Study B](https://example.com/b).",
        "phase": "research_gap",
    },
    {
        "role": "assistant",
        "content": "Also [Study C](https://example.com/c).",
        "phase": "methodology",
    },
]


class TestExtractCitations:
    def test_extracts_markdown_links(self):
        citations = extract_citations_from_messages(MESSAGES_WITH_LINKS)
        urls = [c.url for c in citations]
        assert "https://example.com/a" in urls
        assert "https://example.com/b" in urls
        assert "https://example.com/c" in urls

    def test_ignores_user_messages(self):
        citations = extract_citations_from_messages(MESSAGES_WITH_LINKS)
        urls = [c.url for c in citations]
        assert "https://user.com" not in urls

    def test_deduplication_by_url(self):
        messages = [
            {
                "role": "assistant",
                "content": "[A](https://example.com/a) and [A again](https://example.com/a)",
                "phase": "research_gap",
            },
        ]
        citations = extract_citations_from_messages(messages)
        assert len(citations) == 1

    def test_dedup_with_trailing_slash(self):
        messages = [
            {
                "role": "assistant",
                "content": "[A](https://example.com/a) and [A2](https://example.com/a/)",
                "phase": "research_gap",
            },
        ]
        citations = extract_citations_from_messages(messages)
        assert len(citations) == 1

    def test_first_occurrence_ordering(self):
        citations = extract_citations_from_messages(MESSAGES_WITH_LINKS)
        dynamic = [c for c in citations if not c.is_static]
        assert dynamic[0].title == "Study A"
        assert dynamic[1].title == "Study B"
        assert dynamic[2].title == "Study C"

    def test_sequential_numbering(self):
        citations = extract_citations_from_messages(MESSAGES_WITH_LINKS)
        numbers = [c.number for c in citations]
        assert numbers == list(range(1, len(citations) + 1))

    def test_preserves_source_phase(self):
        citations = extract_citations_from_messages(MESSAGES_WITH_LINKS)
        dynamic = [c for c in citations if not c.is_static]
        assert dynamic[0].source_phase == "research_gap"
        assert dynamic[2].source_phase == "methodology"

    def test_empty_messages_returns_empty(self):
        assert extract_citations_from_messages([]) == []

    def test_user_only_messages_returns_empty(self):
        messages = [{"role": "user", "content": "[Link](https://x.com)", "phase": ""}]
        assert extract_citations_from_messages(messages) == []


# ---------------------------------------------------------------------------
# Static reference matching
# ---------------------------------------------------------------------------

class TestStaticReferenceMatching:
    def test_matches_consort_keyword(self):
        refs = find_matching_references("We followed the CONSORT guidelines.")
        keys = [r.key for r in refs]
        assert "consort" in keys

    def test_matches_strobe_keyword(self):
        refs = find_matching_references("STROBE checklist was used.")
        keys = [r.key for r in refs]
        assert "strobe" in keys

    def test_case_insensitive(self):
        refs = find_matching_references("consort guidelines apply here")
        keys = [r.key for r in refs]
        assert "consort" in keys

    def test_no_match_returns_empty(self):
        refs = find_matching_references("This text has no guideline references.")
        assert refs == []

    def test_merge_static_refs_into_citations(self):
        messages = [
            {
                "role": "assistant",
                "content": "We recommend using the CONSORT checklist for this RCT.",
                "phase": "methodology",
            },
        ]
        citations = extract_citations_from_messages(messages)
        static = [c for c in citations if c.is_static]
        assert len(static) >= 1
        assert any(c.static_ref and c.static_ref.key == "consort" for c in static)

    def test_no_duplicate_if_url_already_inline(self):
        """If an inline link already points to the CONSORT URL, don't add static ref."""
        messages = [
            {
                "role": "assistant",
                "content": (
                    "See [CONSORT](https://www.equator-network.org/reporting-guidelines/consort/) "
                    "for details."
                ),
                "phase": "methodology",
            },
        ]
        citations = extract_citations_from_messages(messages)
        consort_urls = [
            c for c in citations
            if "consort" in _normalize_url(c.url).lower()
        ]
        assert len(consort_urls) == 1


# ---------------------------------------------------------------------------
# Vancouver bibliography formatting
# ---------------------------------------------------------------------------

class TestFormatVancouver:
    def test_empty_citations(self):
        assert format_vancouver_bibliography([]) == ""

    def test_dynamic_citation_format(self):
        citations = [
            Citation(
                number=1,
                title="My Study",
                url="https://example.com/study",
                source_phase="research_gap",
                is_static=False,
            ),
        ]
        result = format_vancouver_bibliography(citations)
        assert result.startswith("1. My Study.")
        assert "Available from: https://example.com/study" in result
        assert "Accessed" in result

    def test_static_citation_format(self):
        from app.data.reference_registry import REFERENCE_REGISTRY
        consort = next(r for r in REFERENCE_REGISTRY if r.key == "consort")
        citations = [
            Citation(
                number=1,
                title=consort.title,
                url=consort.url,
                source_phase="",
                is_static=True,
                static_ref=consort,
            ),
        ]
        result = format_vancouver_bibliography(citations)
        assert "Schulz KF" in result
        assert "BMJ" in result
        assert "2010" in result
        assert "Accessed" not in result

    def test_multiple_citations_numbered(self):
        citations = [
            Citation(number=1, title="A", url="https://a.com", source_phase="", is_static=False),
            Citation(number=2, title="B", url="https://b.com", source_phase="", is_static=False),
        ]
        result = format_vancouver_bibliography(citations)
        lines = result.strip().split("\n")
        assert len(lines) == 2
        assert lines[0].startswith("1.")
        assert lines[1].startswith("2.")
