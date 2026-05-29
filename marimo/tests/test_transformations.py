from __future__ import annotations

import unittest

import pandas as pd

from src.config import DEFAULT_CONFIG
from src.config import INCIDENTS_ONLY_CONFIG
from src.config_io import import_config_from_dict, import_config_to_dict
from src.sample_data import sample_workbook
from src.transformations import (
    build_capability_closure,
    build_capability_tables,
    build_fact_tables,
    build_mapping_tables,
    parse_capability_value,
    split_cell_values,
)


class TransformationTests(unittest.TestCase):
    def test_split_l2_values_with_commas_and_slashes_inside_labels(self) -> None:
        value = (
            "2.4 - Product and Service Enabling/Investment Portfolio Management, "
            "2.5 Product and Service Enabling / Product, Pricing / Billing"
        )

        self.assertEqual(
            split_cell_values(value, code_depth=2),
            [
                "2.4 - Product and Service Enabling/Investment Portfolio Management",
                "2.5 Product and Service Enabling / Product, Pricing / Billing",
            ],
        )

    def test_split_l3_values_with_commas_and_slashes_inside_labels(self) -> None:
        value = (
            "2.4.1 Product and Service Enabling / Investment Portfolio Management / Portfolio, Mandate / Risk, "
            "2.5.1 Product and Service Enabling / Product, Pricing / Billing / Fees, Terms / Conditions"
        )

        self.assertEqual(len(split_cell_values(value, code_depth=3)), 2)

    def test_parse_normalized_capability_value(self) -> None:
        parsed = parse_capability_value("2.4 - Product and Service Enabling/Investment Portfolio Management")

        self.assertIsNotNone(parsed)
        self.assertEqual(parsed.code, "2.4")
        self.assertEqual(parsed.labels, ("Product and Service Enabling", "Investment Portfolio Management"))

    def test_mapping_resolves_by_code(self) -> None:
        workbook = sample_workbook()
        capabilities, capability_warnings = build_capability_tables(workbook, DEFAULT_CONFIG)
        _, _, bridge, mapping_warnings = build_mapping_tables(workbook, DEFAULT_CONFIG, capabilities)

        self.assertEqual(len(capability_warnings), 0)
        self.assertEqual(len(mapping_warnings), 0)
        self.assertEqual(set(bridge["capability_code"]), {"2.4", "2.5", "2.4.1"})

    def test_capability_closure_contains_self_and_ancestors(self) -> None:
        capabilities = pd.DataFrame(
            [
                {"code": "2", "parent_code": ""},
                {"code": "2.4", "parent_code": "2"},
                {"code": "2.4.1", "parent_code": "2.4"},
            ]
        )

        closure = build_capability_closure(capabilities)
        self.assertTrue(((closure["ancestor_code"] == "2") & (closure["descendant_code"] == "2.4.1")).any())
        self.assertTrue(((closure["ancestor_code"] == "2.4.1") & (closure["descendant_code"] == "2.4.1")).any())

    def test_fact_incidents_are_cast_and_validated(self) -> None:
        workbook = {
            "Incidents": pd.DataFrame(
                [
                    {"Application Code": "APP-1", "Year": "2025", "Type": "1", "Incident Count": "3"},
                    {"Application Code": "APP-1", "Year": "2025", "Type": "2", "Incident Count": "2"},
                    {"Application Code": "APP-2", "Year": "2025", "Type": "3", "Incident Count": "1"},
                    {"Application Code": "APP-3", "Year": "not-a-year", "Type": "1", "Incident Count": "1"},
                ]
            )
        }

        fact_tables, warnings = build_fact_tables(workbook, INCIDENTS_ONLY_CONFIG)
        incidents = fact_tables["fact_incidents"]

        self.assertEqual(len(incidents), 2)
        self.assertEqual(list(incidents["incident_type"]), [1, 2])
        self.assertEqual(list(incidents["incident_count"]), [3, 2])
        self.assertGreaterEqual(len(warnings), 2)

    def test_import_config_roundtrip_to_json_shape(self) -> None:
        payload = import_config_to_dict(INCIDENTS_ONLY_CONFIG)
        restored = import_config_from_dict(payload)

        self.assertEqual(restored.fact_sheets[0].target_table, "fact_incidents")
        self.assertEqual(restored.fact_sheets[0].columns[2].allowed_values, (1, 2))


if __name__ == "__main__":
    unittest.main()
