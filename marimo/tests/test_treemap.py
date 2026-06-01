from __future__ import annotations

import unittest

from src.report_helpers import build_treemap_data
from src.sample_data import empty_model, sample_model


class TreemapTests(unittest.TestCase):
    def test_application_metric_counts_distinct_applications_per_capability_ancestor(self) -> None:
        frame = build_treemap_data(sample_model(), "applications")
        capability_weights = frame[frame["kind"] == "capability"].set_index("code")["tree_weight"].to_dict()
        application_rows = frame[frame["kind"] == "application"]

        self.assertEqual(len(application_rows), 1)
        self.assertEqual(set(application_rows["display_label"]), {"Entity 1#APP-NARROW"})
        self.assertEqual(capability_weights["2"], 1)
        self.assertEqual(capability_weights["2.4"], 1)
        self.assertEqual(capability_weights["2.5"], 0)

    def test_incident_metric_sums_incidents_across_years_and_types(self) -> None:
        frame = build_treemap_data(sample_model(), "incidents")
        capability_weights = frame[frame["kind"] == "capability"].set_index("code")["tree_weight"].to_dict()
        application_rows = frame[frame["kind"] == "application"]

        self.assertEqual(len(application_rows), 1)
        self.assertEqual(sorted(application_rows["metric_value"].tolist()), [1.0])
        self.assertEqual(capability_weights["2"], 1)
        self.assertEqual(capability_weights["2.4"], 1)
        self.assertEqual(capability_weights["2.5"], 0)

    def test_empty_incident_metric_stays_empty_without_fact_table(self) -> None:
        frame = build_treemap_data(empty_model(), "incidents")

        self.assertTrue(frame.empty)


if __name__ == "__main__":
    unittest.main()
