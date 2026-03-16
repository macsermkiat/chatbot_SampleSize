"""Tests for protocol export service (DOCX generation)."""

from __future__ import annotations

import io
from unittest.mock import patch

import pytest
from docx import Document

from app.services.protocol_export import (
    _build_protocol_sections,
    generate_docx,
    generate_protocol,
)

SESSION_ID = "550e8400-e29b-41d4-a716-446655440000"

SAMPLE_MESSAGES = [
    {"role": "user", "content": "What study design for statin dementia?", "phase": ""},
    {
        "role": "assistant",
        "content": "Based on literature review, there are gaps in long-term cohort studies.",
        "phase": "research_gap",
    },
    {
        "role": "assistant",
        "content": "A retrospective cohort design using Target Trial Emulation is recommended.",
        "phase": "methodology",
    },
    {
        "role": "assistant",
        "content": "Power analysis: n=1,200 per arm for 80% power at alpha=0.05.",
        "phase": "biostatistics",
    },
]

MESSAGES_WITH_CITATIONS = [
    {"role": "user", "content": "Analyze this topic", "phase": ""},
    {
        "role": "assistant",
        "content": "See [Study X](https://example.com/study-x) for background on CONSORT.",
        "phase": "research_gap",
    },
    {
        "role": "assistant",
        "content": "Based on [Protocol Y](https://example.com/protocol-y).",
        "phase": "methodology",
    },
]


class TestBuildProtocolSections:
    def test_includes_summary_section(self):
        sections = _build_protocol_sections("Summary text", [], SESSION_ID)
        assert len(sections) >= 1
        assert sections[0]["heading"] == "Research Protocol Summary"
        assert sections[0]["content"] == "Summary text"

    def test_includes_phase_sections(self):
        sections = _build_protocol_sections("Summary", SAMPLE_MESSAGES, SESSION_ID)
        headings = [s["heading"] for s in sections]
        assert "Research Gap Analysis" in headings
        assert "Study Methodology" in headings
        assert "Biostatistical Analysis & Sample Size" in headings

    def test_skips_empty_phases(self):
        messages = [
            {"role": "assistant", "content": "Some methodology", "phase": "methodology"},
        ]
        sections = _build_protocol_sections("Summary", messages, SESSION_ID)
        headings = [s["heading"] for s in sections]
        assert "Research Gap Analysis" not in headings
        assert "Study Methodology" in headings
        assert "Biostatistical Analysis & Sample Size" not in headings

    def test_ignores_user_messages(self):
        messages = [
            {"role": "user", "content": "User question", "phase": "research_gap"},
        ]
        sections = _build_protocol_sections("Summary", messages, SESSION_ID)
        # Only summary section, no phase sections from user messages
        assert len(sections) == 1

    def test_empty_messages_returns_summary_only(self):
        sections = _build_protocol_sections("Just the summary", [], SESSION_ID)
        assert len(sections) == 1
        assert sections[0]["content"] == "Just the summary"


class TestGenerateDocx:
    def test_returns_valid_docx_bytes(self):
        result = generate_docx("Test summary", SAMPLE_MESSAGES, SESSION_ID)
        assert isinstance(result, bytes)
        assert len(result) > 0
        # Verify it's a valid DOCX (ZIP format, starts with PK)
        assert result[:2] == b"PK"

    def test_docx_contains_title(self):
        result = generate_docx("Test summary", [], SESSION_ID)
        doc = Document(io.BytesIO(result))
        texts = [p.text for p in doc.paragraphs]
        full_text = "\n".join(texts)
        assert "Research Protocol" in full_text

    def test_docx_contains_summary(self):
        result = generate_docx("My custom summary text", [], SESSION_ID)
        doc = Document(io.BytesIO(result))
        full_text = "\n".join(p.text for p in doc.paragraphs)
        assert "My custom summary text" in full_text

    def test_docx_contains_disclaimer(self):
        result = generate_docx("Summary", [], SESSION_ID)
        doc = Document(io.BytesIO(result))
        full_text = "\n".join(p.text for p in doc.paragraphs)
        assert "Disclaimer" in full_text
        assert "verified" in full_text.lower()

    def test_docx_contains_session_id_prefix(self):
        result = generate_docx("Summary", [], SESSION_ID)
        doc = Document(io.BytesIO(result))
        full_text = "\n".join(p.text for p in doc.paragraphs)
        assert SESSION_ID[:8] in full_text


class TestGenerateProtocol:
    def test_docx_format(self):
        data, content_type, filename = generate_protocol(
            "Summary", SAMPLE_MESSAGES, SESSION_ID, format="docx"
        )
        assert content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        assert filename.endswith(".docx")
        assert SESSION_ID[:8] in filename
        assert isinstance(data, bytes)

    def test_pdf_format_without_weasyprint(self):
        with patch(
            "app.services.protocol_export.generate_pdf",
            side_effect=RuntimeError("PDF export is not available. WeasyPrint is not installed."),
        ):
            with pytest.raises(RuntimeError, match="WeasyPrint"):
                generate_protocol("Summary", [], SESSION_ID, format="pdf")

    def test_default_format_is_docx(self):
        _, content_type, filename = generate_protocol("Summary", [], SESSION_ID)
        assert filename.endswith(".docx")


class TestReferencesInExport:
    def test_docx_contains_references_section_when_links_present(self):
        result = generate_docx("Summary", MESSAGES_WITH_CITATIONS, SESSION_ID)
        doc = Document(io.BytesIO(result))
        full_text = "\n".join(p.text for p in doc.paragraphs)
        assert "References" in full_text
        assert "Study X" in full_text
        assert "example.com/study-x" in full_text

    def test_no_references_section_when_no_citations(self):
        plain_messages = [
            {"role": "assistant", "content": "No links here.", "phase": "methodology"},
        ]
        result = generate_docx("Summary", plain_messages, SESSION_ID)
        doc = Document(io.BytesIO(result))
        headings = [p.text for p in doc.paragraphs if p.style.name.startswith("Heading")]
        assert "References" not in headings

    def test_references_appear_before_disclaimer(self):
        result = generate_docx("Summary", MESSAGES_WITH_CITATIONS, SESSION_ID)
        doc = Document(io.BytesIO(result))
        texts = [p.text for p in doc.paragraphs if p.text.strip()]
        # Find positions
        ref_idx = next(i for i, t in enumerate(texts) if "References" in t)
        disc_idx = next(i for i, t in enumerate(texts) if "Disclaimer" in t)
        assert ref_idx < disc_idx

    def test_static_refs_included_for_keyword_match(self):
        result = generate_docx("Summary", MESSAGES_WITH_CITATIONS, SESSION_ID)
        doc = Document(io.BytesIO(result))
        full_text = "\n".join(p.text for p in doc.paragraphs)
        # CONSORT keyword in messages should trigger static ref
        assert "CONSORT" in full_text
