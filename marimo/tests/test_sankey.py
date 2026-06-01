from __future__ import annotations

import unittest

from src.report_helpers import build_leaf_options, build_level1_options, build_level2_options, build_sankey
from src.coverage import covering_applications_map
from src.sample_data import sample_model


class SankeyWorkbenchTests(unittest.TestCase):
    def test_hierarchical_options_narrow_down_from_l1_to_l3(self) -> None:
        model = sample_model()

        level1 = build_level1_options(model)
        level2 = build_level2_options(model, l1_code="2")
        leaf = build_leaf_options(model, l1_code="2", l2_code="2.4")

        self.assertIn("2 - Product and Service Enabling", level1)
        self.assertEqual(level1["2 - Product and Service Enabling"], "2")
        self.assertIn("2.4 - Investment Portfolio Management", level2)
        self.assertEqual(level2["2.4 - Investment Portfolio Management"], "2.4")
        self.assertIn("2.4.1 - Portfolio, Mandate / Risk", leaf)
        self.assertEqual(leaf["2.4.1 - Portfolio, Mandate / Risk"], "2.4.1")

    def test_covering_applications_are_precomputed_once(self) -> None:
        mapping = covering_applications_map(sample_model(), ["APP-WIDE"])

        self.assertEqual(mapping.iloc[0]["application_code"], "APP-WIDE")
        self.assertEqual(mapping.iloc[0]["covering_applications"], ["Entity 1#APP-NARROW"])

    def test_sankey_uses_compact_labels_for_selected_capabilities(self) -> None:
        figure = build_sankey(sample_model(), capability_codes=["2.4"])
        labels = list(figure.data[0].node.label)

        self.assertIn("Entity 1#APP-WIDE", labels)
        self.assertIn("2.4", labels)


if __name__ == "__main__":
    unittest.main()
