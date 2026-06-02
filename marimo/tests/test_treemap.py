from __future__ import annotations

import unittest

import pandas as pd

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

    def test_application_metric_filters_by_entity(self) -> None:
        model = _multi_entity_model()
        frame = build_treemap_data(model, "applications", entity_code="Entity 2")
        application_rows = frame[frame["kind"] == "application"]

        self.assertEqual(set(application_rows["entity_code"]), {"Entity 2"})
        self.assertEqual(set(application_rows["application_code"]), {"APP-OTHER"})

    def test_incident_metric_filters_years_and_types(self) -> None:
        model = _multi_entity_model()
        frame = build_treemap_data(
            model,
            "incidents",
            incident_years=[2025],
            incident_types=[1],
        )
        application_rows = frame[frame["kind"] == "application"]

        self.assertEqual(set(application_rows["application_code"]), {"APP-NARROW"})
        self.assertEqual(sorted(application_rows["metric_value"].tolist()), [1.0])

    def test_incident_metric_normalizes_by_application_count(self) -> None:
        model = _multi_entity_model()
        frame = build_treemap_data(model, "incidents", normalize_incidents=True)
        capability_row = frame[(frame["kind"] == "capability") & (frame["code"] == "2.4.1")].iloc[0]

        self.assertEqual(capability_row["application_count"], 2)
        self.assertEqual(capability_row["incident_total"], 16)
        self.assertEqual(capability_row["metric_value"], 8.0)
        self.assertEqual(capability_row["normalized_metric_value"], 8.0)
def _multi_entity_model() -> dict[str, pd.DataFrame]:
    model = sample_model()
    model["dim_entity"] = pd.concat(
        [
            model["dim_entity"],
            pd.DataFrame([{"entity_code": "Entity 2", "label": "Entity 2"}]),
        ],
        ignore_index=True,
    )
    model["dim_application"] = pd.concat(
        [
            model["dim_application"],
            pd.DataFrame(
                [
                    {
                        "application_code": "APP-OTHER",
                        "application_name": "Other App",
                        "display_name": "Other App",
                        "entity_code": "Entity 2",
                    }
                ]
            ),
        ],
        ignore_index=True,
    )
    model["bridge_application_capability"] = pd.concat(
        [
            model["bridge_application_capability"],
            pd.DataFrame(
                [
                    {
                        "application_code": "APP-OTHER",
                        "entity_code": "Entity 2",
                        "capability_code": "2.4.1",
                        "mapped_level": "L3",
                        "source_sheet": "E2-BCM",
                        "source_row": 99,
                    }
                ]
            ),
        ],
        ignore_index=True,
    )
    model["fact_incidents"] = pd.DataFrame(
        [
            {"application_code": "APP-NARROW", "year": 2024, "incident_type": 1, "incident_count": 10, "source_sheet": "Incidents", "source_row": 2},
            {"application_code": "APP-NARROW", "year": 2025, "incident_type": 1, "incident_count": 1, "source_sheet": "Incidents", "source_row": 3},
            {"application_code": "APP-OTHER", "year": 2025, "incident_type": 2, "incident_count": 5, "source_sheet": "Incidents", "source_row": 4},
        ],
        columns=["application_code", "year", "incident_type", "incident_count", "source_sheet", "source_row"],
    )
    return model


if __name__ == "__main__":
    unittest.main()
