"""Tests for app.services.memory.trim_messages -- pure Python."""

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from app.services.memory import trim_messages


class TestTrimMessages:
    def test_short_list_unchanged(self):
        msgs = [HumanMessage(content="hello")]
        result = trim_messages(msgs, window=20)
        assert len(result) == 1
        assert result[0].content == "hello"

    def test_exact_window_unchanged(self):
        msgs = [HumanMessage(content=f"msg{i}") for i in range(20)]
        result = trim_messages(msgs, window=20)
        assert len(result) == 20

    def test_over_window_truncated(self):
        msgs = [HumanMessage(content=f"msg{i}") for i in range(25)]
        result = trim_messages(msgs, window=20)
        assert len(result) == 20
        assert result[0].content == "msg5"
        assert result[-1].content == "msg24"

    def test_system_message_preserved(self):
        msgs = [SystemMessage(content="system")] + [
            HumanMessage(content=f"msg{i}") for i in range(25)
        ]
        result = trim_messages(msgs, window=20)
        assert len(result) == 20
        assert result[0].content == "system"
        assert getattr(result[0], "type", None) == "system"

    def test_custom_window_size(self):
        msgs = [HumanMessage(content=f"msg{i}") for i in range(10)]
        result = trim_messages(msgs, window=5)
        assert len(result) == 5
        assert result[0].content == "msg5"

    def test_empty_list(self):
        result = trim_messages([], window=20)
        assert result == []
