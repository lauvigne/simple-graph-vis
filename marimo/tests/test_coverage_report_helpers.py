from __future__ import annotations

import unittest

from src.report_helpers import coverage_candidates_display, covering_applications_detail
from src.sample_data import sample_model


class CoverageReportHelpersTests(unittest.TestCase):
    def test_coverage_candidate_display_enriches_labels(self) -> None:
        frame = coverage_candidates_display(sample_model(), threshold=0.5, entity=None, scope_mode="all")

        self.assertFalse(frame.empty)
        self.assertIn("covered_application_detail", frame.columns)
        self.assertIn("covering_application_detail", frame.columns)
        self.assertEqual(frame.iloc[0]["covered_application_detail"], "Entity 1#APP-NARROW - Narrow App")
        self.assertEqual(frame.iloc[0]["covering_application_detail"], "Entity 1#APP-WIDE - Wide App")

    def test_covering_applications_detail_lists_applications(self) -> None:
        frame = covering_applications_detail(sample_model(), "APP-NARROW")

        self.assertEqual(len(frame), 1)
        self.assertEqual(frame.iloc[0]["application_code"], "APP-WIDE")
        self.assertEqual(frame.iloc[0]["application_detail"], "Entity 1#APP-WIDE - Wide App")


if __name__ == "__main__":
    unittest.main()
