"""Tests for app.agents.helpers -- pure Python, no mocks needed."""

from langchain_core.messages import AIMessage, HumanMessage

from app.agents.helpers import build_input_text, get_latest_user_message
from tests.conftest import base_state


# ---------------------------------------------------------------------------
# get_latest_user_message
# ---------------------------------------------------------------------------

class TestGetLatestUserMessage:
    def test_returns_last_human_message(self):
        state = base_state(messages=[
            HumanMessage(content="first"),
            AIMessage(content="response"),
            HumanMessage(content="second"),
        ])
        assert get_latest_user_message(state) == "second"

    def test_returns_dash_when_no_human(self):
        state = base_state(messages=[AIMessage(content="only AI")])
        assert get_latest_user_message(state) == "-"

    def test_returns_dash_when_empty(self):
        state = base_state(messages=[])
        assert get_latest_user_message(state) == "-"


# ---------------------------------------------------------------------------
# build_input_text
# ---------------------------------------------------------------------------

class TestBuildInputText:
    def test_with_forwarded_message(self):
        state = base_state(
            forwarded_message="context from orchestrator",
            messages=[HumanMessage(content="user question")],
        )
        result = build_input_text(state)
        assert "context from orchestrator" in result
        assert "user question" in result

    def test_without_forwarded_message(self):
        state = base_state(
            forwarded_message="",
            messages=[HumanMessage(content="hello")],
        )
        result = build_input_text(state)
        assert "Query from other agent: -" in result
        assert "hello" in result

    def test_none_forwarded_message(self):
        state = base_state(messages=[HumanMessage(content="hi")])
        state["forwarded_message"] = None
        result = build_input_text(state)
        assert "Query from other agent: -" in result
