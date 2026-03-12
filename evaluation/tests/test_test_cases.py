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
    def test_loads_cases(self):
        cases = _load_cases("methodology_cases.json")
        assert len(cases) == 24

    def test_multi_turn_cases_exist(self):
        cases = _load_cases("methodology_cases.json")
        multi_turn = [c for c in cases if c.follow_up_prompts]
        assert len(multi_turn) == 24

    def test_kept_cases_preserved(self):
        cases = _load_cases("methodology_cases.json")
        case_ids = sorted(c.case_id for c in cases)
        for cid in ["M02", "M04", "M06", "M07", "M09", "M10", "M13", "M14", "M17", "M18", "M20"]:
            assert cid in case_ids

    def test_new_cases_present(self):
        cases = _load_cases("methodology_cases.json")
        case_ids = sorted(c.case_id for c in cases)
        for cid in ["M21", "M22", "M23", "M24", "M25", "M26", "M27", "M28", "M29", "M30", "M31", "M32", "M33"]:
            assert cid in case_ids

    def test_removed_cases_absent(self):
        cases = _load_cases("methodology_cases.json")
        case_ids = [c.case_id for c in cases]
        for cid in ["M01", "M03", "M05", "M08", "M11", "M12", "M15", "M16", "M19"]:
            assert cid not in case_ids


class TestBiostatisticsCases:
    def test_loads_cases(self):
        cases = _load_cases("biostatistics_cases.json")
        assert len(cases) == 24

    def test_multi_turn_cases_exist(self):
        cases = _load_cases("biostatistics_cases.json")
        multi_turn = [c for c in cases if c.follow_up_prompts]
        assert len(multi_turn) == 24

    def test_b02_has_three_turn_chain(self):
        cases = _load_cases("biostatistics_cases.json")
        b02 = next(c for c in cases if c.case_id == "B02")
        assert len(b02.follow_up_prompts) == 2

    def test_kept_cases_preserved(self):
        cases = _load_cases("biostatistics_cases.json")
        case_ids = sorted(c.case_id for c in cases)
        for cid in ["B02", "B03", "B04", "B05", "B09", "B10", "B11", "B13", "B14", "B15", "B18", "B20"]:
            assert cid in case_ids

    def test_new_cases_present(self):
        cases = _load_cases("biostatistics_cases.json")
        case_ids = sorted(c.case_id for c in cases)
        for cid in ["B21", "B22", "B23", "B24", "B25", "B26", "B27", "B28", "B29", "B30", "B31", "B32"]:
            assert cid in case_ids

    def test_removed_cases_absent(self):
        cases = _load_cases("biostatistics_cases.json")
        case_ids = [c.case_id for c in cases]
        for cid in ["B01", "B06", "B07", "B08", "B12", "B16", "B17", "B19"]:
            assert cid not in case_ids


class TestEdgeCases:
    def test_loads_cases(self):
        cases = _load_cases("edge_cases.json")
        assert len(cases) == 6

    def test_multi_turn_cases_exist(self):
        cases = _load_cases("edge_cases.json")
        multi_turn = [c for c in cases if c.follow_up_prompts]
        assert len(multi_turn) == 4

    def test_e02_recovery_flow(self):
        cases = _load_cases("edge_cases.json")
        e02 = next(c for c in cases if c.case_id == "E02")
        assert len(e02.follow_up_prompts) == 1
        # Follow-up should provide the missing parameters
        assert "type 2 diabetes" in e02.follow_up_prompts[0].lower()

    def test_removed_cases_absent(self):
        cases = _load_cases("edge_cases.json")
        case_ids = [c.case_id for c in cases]
        for cid in ["E05", "E06", "E07", "E10"]:
            assert cid not in case_ids


class TestAllCases:
    def test_total_case_count(self):
        meth = _load_cases("methodology_cases.json")
        bio = _load_cases("biostatistics_cases.json")
        edge = _load_cases("edge_cases.json")
        assert len(meth) + len(bio) + len(edge) == 54

    def test_total_multi_turn_count(self):
        all_cases: list[TestCase] = []
        for f in ("methodology_cases.json", "biostatistics_cases.json", "edge_cases.json"):
            all_cases.extend(_load_cases(f))
        multi_turn = [c for c in all_cases if c.follow_up_prompts]
        # 24 + 24 + 4 = 52 multi-turn out of 54 total (96%)
        assert len(multi_turn) >= 50

    def test_follow_up_prompts_are_strings(self):
        all_cases: list[TestCase] = []
        for f in ("methodology_cases.json", "biostatistics_cases.json", "edge_cases.json"):
            all_cases.extend(_load_cases(f))
        for case in all_cases:
            for prompt in case.follow_up_prompts:
                assert isinstance(prompt, str)
                assert len(prompt) > 0
