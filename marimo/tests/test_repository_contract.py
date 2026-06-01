from __future__ import annotations

import unittest

from src.duckdb_repository import TABLES


class RepositoryContractTests(unittest.TestCase):
    def test_expected_tables_are_declared(self) -> None:
        self.assertEqual(
            set(TABLES),
            {
                "dim_business_capability",
                "dim_application",
                "dim_entity",
                "bridge_application_capability",
                "capability_closure",
                "import_warnings",
            },
        )


if __name__ == "__main__":
    unittest.main()
