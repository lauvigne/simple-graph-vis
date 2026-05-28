from __future__ import annotations

import unittest

from src.coverage import coverage_candidates
from src.sample_data import sample_model


class CoverageTests(unittest.TestCase):
    def test_coverage_candidates_are_computed(self) -> None:
        candidates = coverage_candidates(sample_model(), threshold=0.5, scope_mode="all")

        self.assertGreater(len(candidates), 0)
        self.assertIn("coverage", candidates.columns)

    def test_cross_entity_filter_can_return_empty_without_failing(self) -> None:
        candidates = coverage_candidates(sample_model(), threshold=0.5, scope_mode="crossEntity")

        self.assertEqual(list(candidates.columns), [
            "application_code_covered",
            "entity_code_covered",
            "application_code_covering",
            "entity_code_covering",
            "overlap_count",
            "covered_count",
            "covering_count",
            "coverage",
            "type",
        ])


if __name__ == "__main__":
    unittest.main()
