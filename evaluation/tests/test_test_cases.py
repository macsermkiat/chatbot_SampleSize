"""Tests for test case bank validation, including multi-turn cases."""

import json
from pathlib import Path

from evaluation.test_cases.schema import TestCase


BASE = Path(__file__).resolve().parent.parent / "test_cases"


def _load_cases(filename: str) -> list[TestCase]:
    filepath = BASE / filename
    raw = json.loads(filepath.read_text())
    items = raw if isinstance(raw, list) else raw.get("cases", [])
    return [TestCase.model_validate(item) for item in items]


class TestMethodologyCases:
    def test_loads_20_cases(self):
        cases = _load_cases("methodology_cases.json")
        assert len(cases) == 20

    def test_multi_turn_cases_exist(self):
        cases = _load_cases("methodology_cases.json")
        multi_turn = [c for c in cases if c.follow_up_prompts]
        assert len(multi_turn) == 5

    def test_multi_turn_case_ids(self):
        cases = _load_cases("methodology_cases.json")
        multi_turn_ids = sorted(
            c.case_id for c in cases if c.follow_up_prompts
        )
        assert multi_turn_ids == ["M02", "M05", "M08", "M12", "M16"]

    def test_m05_has_two_follow_ups(self):
        cases = _load_cases("methodology_cases.json")
        m05 = next(c for c in cases if c.case_id == "M05")
        assert len(m05.follow_up_prompts) == 2

    def test_m16_has_cross_phase_follow_up(self):
        cases = _load_cases("methodology_cases.json")
        m16 = next(c for c in cases if c.case_id == "M16")
        assert len(m16.follow_up_prompts) == 2
        assert "sample size" in m16.follow_up_prompts[-1].lower()


class TestBiostatisticsCases:
    def test_loads_20_cases(self):
        cases = _load_cases("biostatistics_cases.json")
        assert len(cases) == 20

    def test_multi_turn_cases_exist(self):
        cases = _load_cases("biostatistics_cases.json")
        multi_turn = [c for c in cases if c.follow_up_prompts]
        # Original 4 (B01, B03, B06, B18) + new 5 (B02, B07, B10, B14, B19)
        assert len(multi_turn) == 9

    def test_b02_has_three_turn_chain(self):
        cases = _load_cases("biostatistics_cases.json")
        b02 = next(c for c in cases if c.case_id == "B02")
        assert len(b02.follow_up_prompts) == 2


class TestEdgeCases:
    def test_loads_10_cases(self):
        cases = _load_cases("edge_cases.json")
        assert len(cases) == 10

    def test_multi_turn_cases_exist(self):
        cases = _load_cases("edge_cases.json")
        multi_turn = [c for c in cases if c.follow_up_prompts]
        assert len(multi_turn) == 3

    def test_e02_recovery_flow(self):
        cases = _load_cases("edge_cases.json")
        e02 = next(c for c in cases if c.case_id == "E02")
        assert len(e02.follow_up_prompts) == 1
        # Follow-up should provide the missing parameters
        assert "type 2 diabetes" in e02.follow_up_prompts[0].lower()


class TestAllCases:
    def test_total_case_count(self):
        meth = _load_cases("methodology_cases.json")
        bio = _load_cases("biostatistics_cases.json")
        edge = _load_cases("edge_cases.json")
        assert len(meth) + len(bio) + len(edge) == 50

    def test_total_multi_turn_count(self):
        all_cases: list[TestCase] = []
        for f in ("methodology_cases.json", "biostatistics_cases.json", "edge_cases.json"):
            all_cases.extend(_load_cases(f))
        multi_turn = [c for c in all_cases if c.follow_up_prompts]
        assert len(multi_turn) == 17  # 5 + 9 + 3

    def test_follow_up_prompts_are_strings(self):
        all_cases: list[TestCase] = []
        for f in ("methodology_cases.json", "biostatistics_cases.json", "edge_cases.json"):
            all_cases.extend(_load_cases(f))
        for case in all_cases:
            for prompt in case.follow_up_prompts:
                assert isinstance(prompt, str)
                assert len(prompt) > 0
