"""Tests for formatting helpers in app.agents.research_gap -- pure Python."""

from app.agents.research_gap import _extract_domain, _format_progress, _format_search_results
from app.services.tavily import SearchResult


# ---------------------------------------------------------------------------
# _format_search_results
# ---------------------------------------------------------------------------

class TestFormatSearchResults:
    def test_empty_results(self):
        assert _format_search_results([]) == "No search results available."

    def test_single_result(self):
        results = [{"title": "Study A", "url": "https://example.com", "content": "content", "score": 0.9}]
        formatted = _format_search_results(results)
        assert "Study A" in formatted
        assert "https://example.com" in formatted
        assert "0.90" in formatted

    def test_multiple_results(self):
        results = [
            {"title": "Study A", "url": "https://a.com", "content": "a", "score": 0.9},
            {"title": "Study B", "url": "https://b.com", "content": "b", "score": 0.8},
        ]
        formatted = _format_search_results(results)
        assert "1." in formatted
        assert "2." in formatted

    def test_missing_fields(self):
        results = [{}]
        formatted = _format_search_results(results)
        assert "Untitled" in formatted
        assert "0.00" in formatted


# ---------------------------------------------------------------------------
# _format_progress
# ---------------------------------------------------------------------------

class TestFormatProgress:
    def test_with_results_advanced(self):
        queries = ["term1"]
        results = [SearchResult(url="https://example.com", title="Title", content="content", score=0.9)]
        progress = _format_progress(queries, results, "advanced")
        assert "term1" in progress
        assert "Title" in progress
        assert "Found 1 sources" in progress

    def test_with_results_simple_hides_terms(self):
        queries = ["(\"Sepsis\"[MeSH]) AND randomized"]
        results = [SearchResult(url="https://example.com", title="Title", content="content", score=0.9)]
        progress = _format_progress(queries, results, "simple")
        # Simple mode should NOT show raw MeSH search terms
        assert "MeSH" not in progress
        assert "Title" in progress
        assert "Searching for relevant studies" in progress

    def test_without_results(self):
        progress = _format_progress(["term1"], [])
        assert "No results found" in progress


# ---------------------------------------------------------------------------
# _extract_domain
# ---------------------------------------------------------------------------

class TestExtractDomain:
    def test_normal_url(self):
        assert _extract_domain("https://pubmed.ncbi.nlm.nih.gov/123") == "pubmed.ncbi.nlm.nih.gov"

    def test_www_stripped(self):
        assert _extract_domain("https://www.example.com/page") == "example.com"

    def test_empty_string(self):
        assert _extract_domain("") == ""

    def test_invalid_url(self):
        assert _extract_domain("not-a-url") == ""
