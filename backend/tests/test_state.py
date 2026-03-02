"""Tests for app.agents.state -- Pydantic schema validation."""

import pytest
from pydantic import ValidationError

from app.agents.state import (
    BiostatisticsOutput,
    CodingOutput,
    GapSearchOutput,
    GapSummarizeOutput,
    MethodologyOutput,
    OrchestratorOutput,
)


class TestOrchestratorOutput:
    def test_valid_construction(self):
        out = OrchestratorOutput(direct_response_to_user="hello")
        assert out.direct_response_to_user == "hello"
        assert out.needs_clarification is False
        assert out.agent_to_route_to == ""
        assert out.forwarded_message == ""

    def test_missing_required_field(self):
        with pytest.raises(ValidationError):
            OrchestratorOutput()


class TestGapSearchOutput:
    def test_valid_terms(self):
        out = GapSearchOutput(terms=["term1", "term2", "term3"])
        assert len(out.terms) == 3

    def test_missing_terms(self):
        with pytest.raises(ValidationError):
            GapSearchOutput()


class TestGapSummarizeOutput:
    def test_defaults(self):
        out = GapSummarizeOutput(direct_response_to_user="summary")
        assert out.agent_to_route_to == ""
        assert out.forwarded_message == ""


class TestMethodologyOutput:
    def test_defaults(self):
        out = MethodologyOutput(direct_response_to_user="design")
        assert out.agent_to_route_to == ""
        assert out.forwarded_message == ""


class TestBiostatisticsOutput:
    def test_defaults(self):
        out = BiostatisticsOutput(direct_response_to_user="stats")
        assert out.need_info is False
        assert out.diagnostic_query == ""
        assert out.forwarded_message == ""
        assert out.session_id == ""


class TestCodingOutput:
    def test_defaults(self):
        out = CodingOutput(direct_response_to_user="code")
        assert out.python_script == ""
        assert out.agent_to_route_to == ""
        assert out.forwarded_message == ""
        assert out.session_id == ""

    def test_with_script(self):
        out = CodingOutput(
            direct_response_to_user="result",
            python_script="print(42)",
        )
        assert out.python_script == "print(42)"
