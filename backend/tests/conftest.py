"""Shared test fixtures for the research assistant backend."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from langchain_core.messages import HumanMessage


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
        "session_id": "test-session",
        "uploaded_files": [],
        "code_output": {},
        "search_results": [],
        "search_count": 0,
        "expertise_level": "advanced",
        "execution_result": {},
        "stored_python_script": "",
        "has_pending_code": False,
    }
    return {**defaults, **overrides}


# ---------------------------------------------------------------------------
# Mock LLM builders
# ---------------------------------------------------------------------------

def make_mock_llm(return_value: Any) -> MagicMock:
    """Build a mock that mimics ``get_chat_model().with_structured_output().ainvoke()``.

    Used for tests that manually patch ``get_chat_model`` (e.g. diagnostic tool,
    R/STATA translation).
    """
    inner = AsyncMock(return_value=return_value)
    structured = MagicMock()
    structured.ainvoke = inner
    llm = MagicMock()
    llm.with_structured_output.return_value = structured
    # For non-structured calls (e.g., diagnostic tool)
    llm.ainvoke = AsyncMock(return_value=MagicMock(content="diagnostic result"))
    return llm


def make_mock_structured_llm(return_value: Any) -> MagicMock:
    """Build a mock that mimics ``get_structured_model()`` return value.

    The returned mock has ``.ainvoke()`` that returns *return_value* directly,
    matching the behavior of a model with structured output already applied.
    """
    mock = MagicMock()
    mock.ainvoke = AsyncMock(return_value=return_value)
    return mock


# ---------------------------------------------------------------------------
# Reusable patch fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def patch_get_chat_model():
    """Yields a function that patches get_structured_model for a given module path.

    Most agent nodes use ``get_structured_model`` (which returns a model with
    structured output already applied). This fixture patches that import.
    """
    patches: list[Any] = []
    mocks: list[MagicMock] = []

    def _patch(module_path: str, return_value: Any) -> MagicMock:
        mock = make_mock_structured_llm(return_value)
        mocks.append(mock)
        p = patch(f"{module_path}.get_structured_model", return_value=mock)
        patches.append(p)
        p.start()
        return mock

    yield _patch

    for p in patches:
        p.stop()


@pytest.fixture()
def patch_tavily_search():
    """Patches app.agents.research_gap.search with a mock returning given results.

    Auto-cleans up on teardown -- callers do NOT need to stop the patcher.
    """
    from app.services.tavily import SearchResult

    patches: list[Any] = []

    def _patch(results: list[SearchResult] | None = None) -> AsyncMock:
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
        patches.append(p)
        p.start()
        return mock

    yield _patch

    for p in patches:
        p.stop()
