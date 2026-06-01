from __future__ import annotations

import unittest

from src.report_helpers import build_hierarchical_sankey
from src.sample_data import sample_model


class HierarchicalSankeyTests(unittest.TestCase):
    def test_hierarchical_sankey_orders_entity_application_l3_l2(self) -> None:
        figure = build_hierarchical_sankey(sample_model(), capability_codes=["2.4"])
        labels = list(figure.data[0].node.label)
        links = [
            (labels[source], labels[target])
            for source, target in zip(figure.data[0].link.source, figure.data[0].link.target)
        ]

        self.assertIn("Entity 1", labels)
        self.assertIn("Entity 1#APP-WIDE", labels)
        self.assertIn("Entity 1#APP-NARROW", labels)
        self.assertIn("2.4.1", labels)
        self.assertIn("2.4", labels)
        self.assertNotIn("2.5", labels)

        self.assertIn(("Entity 1", "Entity 1#APP-WIDE"), links)
        self.assertIn(("Entity 1", "Entity 1#APP-NARROW"), links)
        self.assertIn(("Entity 1#APP-WIDE", "2.4"), links)
        self.assertIn(("Entity 1#APP-NARROW", "2.4.1"), links)
        self.assertIn(("2.4.1", "2.4"), links)

    def test_hierarchical_sankey_falls_back_to_direct_l2_links(self) -> None:
        figure = build_hierarchical_sankey(sample_model(), capability_codes=["2.5"])
        labels = list(figure.data[0].node.label)
        links = [
            (labels[source], labels[target])
            for source, target in zip(figure.data[0].link.source, figure.data[0].link.target)
        ]

        self.assertIn("Entity 1#APP-WIDE", labels)
        self.assertIn("2.5", labels)
        self.assertIn(("Entity 1#APP-WIDE", "2.5"), links)


if __name__ == "__main__":
    unittest.main()
