from __future__ import annotations

import unittest

from src.report_helpers import build_treemap_data
from src.sample_data import empty_model, sample_model


class TreemapTests(unittest.TestCase):
    def test_application_metric_counts_distinct_applications_per_capability_ancestor(self) -> None:
        frame = build_treemap_data(sample_model(), "applications")
        values = dict(zip(frame["code"], frame["metric_value"]))
        weights = dict(zip(frame["code"], frame["tree_weight"]))

        self.assertEqual(values["2.4"], 1)
        self.assertEqual(values["2.5"], 1)
        self.assertEqual(values["2.4.1"], 1)
        self.assertEqual(weights["2"], 3)
        self.assertEqual(weights["2.4"], 2)
        self.assertEqual(weights["2.5"], 1)

    def test_incident_metric_sums_incidents_across_years_and_types(self) -> None:
        frame = build_treemap_data(sample_model(), "incidents")
        values = dict(zip(frame["code"], frame["metric_value"]))
        weights = dict(zip(frame["code"], frame["tree_weight"]))

        self.assertEqual(values["2.4"], 6)
        self.assertEqual(values["2.5"], 6)
        self.assertEqual(values["2.4.1"], 1)
        self.assertEqual(weights["2"], 13)
        self.assertEqual(weights["2.4"], 7)
        self.assertEqual(weights["2.5"], 6)

    def test_empty_incident_metric_stays_empty_without_fact_table(self) -> None:
        frame = build_treemap_data(empty_model(), "incidents")

        self.assertTrue(frame.empty)


if __name__ == "__main__":
    unittest.main()
