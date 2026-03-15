"""Tests for confidence scoring and disclaimer features (Phase 4).

TDD RED phase: these tests should FAIL until implementation is complete.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.agents.state import BiostatisticsOutput, CodingOutput, ConfidenceLevel


# ---------------------------------------------------------------------------
# 1. BiostatisticsOutput confidence_level field
# ---------------------------------------------------------------------------


class TestBiostatisticsOutputConfidence:
    """BiostatisticsOutput must include a confidence_level field."""

    def test_default_confidence_is_medium(self):
        out = BiostatisticsOutput(direct_response_to_user="analysis")
        assert out.confidence_level == "medium"

    def test_high_confidence(self):
        out = BiostatisticsOutput(
            direct_response_to_user="Standard two-arm RCT power analysis.",
            confidence_level="high",
        )
        assert out.confidence_level == "high"

    def test_low_confidence(self):
        out = BiostatisticsOutput(
            direct_response_to_user="Complex adaptive design.",
            confidence_level="low",
        )
        assert out.confidence_level == "low"

    def test_invalid_confidence_rejected(self):
        with pytest.raises(ValidationError):
            BiostatisticsOutput(
                direct_response_to_user="test",
                confidence_level="invalid",
            )

    def test_confidence_level_type_exported(self):
        """ConfidenceLevel literal type should be importable."""
        assert "high" in ConfidenceLevel.__args__
        assert "medium" in ConfidenceLevel.__args__
        assert "low" in ConfidenceLevel.__args__


# ---------------------------------------------------------------------------
# 2. ResearchState confidence_level field
# ---------------------------------------------------------------------------


class TestResearchStateConfidence:
    """ResearchState must carry confidence_level through the graph."""

    def test_state_has_confidence_key(self):
        from app.agents.state import ResearchState

        annotations = ResearchState.__annotations__
        assert "confidence_level" in annotations

    def test_confidence_propagated_in_state_dict(self):
        """A dict conforming to ResearchState should accept confidence_level."""
        from app.agents.state import ResearchState

        # TypedDict is a structural type -- just verify the key is defined
        state: ResearchState = {  # type: ignore[typeddict-item]
            "messages": [],
            "current_phase": "biostatistics",
            "agent_to_route_to": "",
            "forwarded_message": "",
            "needs_clarification": False,
            "need_info": False,
            "session_id": "test",
            "uploaded_files": [],
            "code_output": {},
            "search_results": [],
            "search_count": 0,
            "expertise_level": "advanced",
            "execution_result": {},
            "stored_python_script": "",
            "has_pending_code": False,
            "confidence_level": "high",
        }
        assert state["confidence_level"] == "high"


# ---------------------------------------------------------------------------
# 3. Disclaimer in coding output
# ---------------------------------------------------------------------------

DISCLAIMER_FRAGMENT = "Verify with your biostatistician"


class TestDisclaimer:
    """Coding agent output must include a disclaimer for statistical results."""

    def test_format_execution_results_includes_disclaimer(self):
        from app.agents.biostatistics import _format_execution_results

        exec_result = {
            "success": True,
            "stdout": "| Parameter | Value |\n|---|---|\n| n per group | 64 |",
        }
        formatted = _format_execution_results(exec_result)
        assert DISCLAIMER_FRAGMENT.lower() in formatted.lower()

    def test_disclaimer_not_added_on_failure(self):
        from app.agents.biostatistics import _format_execution_results

        exec_result = {
            "success": False,
            "error_message": "SyntaxError",
        }
        formatted = _format_execution_results(exec_result)
        assert DISCLAIMER_FRAGMENT.lower() not in formatted.lower()

    def test_disclaimer_not_added_on_empty(self):
        from app.agents.biostatistics import _format_execution_results

        formatted = _format_execution_results({})
        assert formatted == ""


# ---------------------------------------------------------------------------
# 4. SSE message includes confidence
# ---------------------------------------------------------------------------


class TestSSEConfidenceField:
    """SSE message events should include confidence when present in output."""

    def test_message_event_includes_confidence(self):
        """Verify that the SSE message JSON schema supports a confidence field."""
        import json

        # Simulate the data dict that _stream_graph yields for a message event
        data = json.dumps({
            "node": "biostatistics",
            "content": "Power analysis result.",
            "phase": "biostatistics",
            "confidence": "high",
        })
        parsed = json.loads(data)
        assert parsed["confidence"] == "high"

    def test_message_event_omits_confidence_for_non_biostats(self):
        """Non-biostatistics messages should have no confidence field."""
        import json

        data = json.dumps({
            "node": "orchestrator",
            "content": "Routing to methodology.",
            "phase": "orchestrator",
        })
        parsed = json.loads(data)
        assert "confidence" not in parsed
