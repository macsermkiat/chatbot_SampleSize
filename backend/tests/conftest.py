"""Shared test fixtures for the research assistant backend."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from langchain_core.messages import HumanMessage

from app.agents.state import ResearchState


# ---------------------------------------------------------------------------
# State factory
# ---------------------------------------------------------------------------

def base_state(**overrides: Any) -> dict:
    """Return a minimal ResearchState dict with sensible defaults.

    Accepts keyword overrides for any field.
    """
    defaults: dict[str, Any] = {
        "messages": [HumanMessage(content="test query")],
        "current_phase": "orchestrator",
        "agent_to_route_to": "",
        "forwarded_message": "",
        "needs_clarification": False,
        "need_info": False,
        "need_code": False,
        "session_id": "test-session",
        "uploaded_files": [],
        "code_output": {},
        "search_results": [],
        "search_count": 0,
    }
    return {**defaults, **overrides}


# ---------------------------------------------------------------------------
# Mock LLM builder
# ---------------------------------------------------------------------------

def make_mock_llm(return_value: Any) -> MagicMock:
    """Build a mock that mimics ``get_chat_model().with_structured_output().ainvoke()``.

    Usage::

        mock = make_mock_llm(OrchestratorOutput(direct_response_to_user="hi"))
        with patch("app.agents.orchestrator.get_chat_model", return_value=mock):
            result = await orchestrator_node(state)
    """
    inner = AsyncMock(return_value=return_value)
    structured = MagicMock()
    structured.ainvoke = inner
    llm = MagicMock()
    llm.with_structured_output.return_value = structured
    # For non-structured calls (e.g., diagnostic tool)
    llm.ainvoke = AsyncMock(return_value=MagicMock(content="diagnostic result"))
    return llm


# ---------------------------------------------------------------------------
# Reusable patch fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def patch_get_chat_model():
    """Yields a function that patches get_chat_model for a given module path.

    Clears the lru_cache on teardown.
    """
    patches: list[Any] = []

    def _patch(module_path: str, return_value: Any) -> MagicMock:
        mock = make_mock_llm(return_value)
        p = patch(f"{module_path}.get_chat_model", return_value=mock)
        patches.append(p)
        p.start()
        return mock

    yield _patch

    for p in patches:
        p.stop()

    # Clear LLM cache
    from app.services.llm import get_chat_model
    get_chat_model.cache_clear()


@pytest.fixture()
def patch_tavily_search():
    """Patches app.agents.research_gap.search with a mock returning given results."""
    from app.services.tavily import SearchResult

    def _patch(results: list[SearchResult] | None = None):
        if results is None:
            results = [
                SearchResult(
                    url="https://pubmed.ncbi.nlm.nih.gov/123",
                    title="Test Study",
                    content="Study about testing.",
                    score=0.95,
                ),
            ]
        mock = AsyncMock(return_value=results)
        p = patch("app.agents.research_gap.search", mock)
        p.start()
        return p, mock

    yield _patch
