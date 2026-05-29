from __future__ import annotations

import pandas as pd

from .config import DEFAULT_CONFIG
from .transformations import build_model


def sample_workbook() -> dict[str, pd.DataFrame]:
    return {
        "BIAN Capabilities": pd.DataFrame(
            [
                {
                    "Business Capability (L1)": "Product and Service Enabling",
                    "Business Capability (L2)": "Investment Portfolio Management",
                    "Business Capability (L3)": "",
                    "Business Capability (L2) long name": "2.4 Product and Service Enabling / Investment Portfolio Management",
                    "Business Capability (L3) long name": "",
                },
                {
                    "Business Capability (L1)": "Product and Service Enabling",
                    "Business Capability (L2)": "Product, Pricing / Billing",
                    "Business Capability (L3)": "",
                    "Business Capability (L2) long name": "2.5 Product and Service Enabling / Product, Pricing / Billing",
                    "Business Capability (L3) long name": "",
                },
                {
                    "Business Capability (L1)": "Product and Service Enabling",
                    "Business Capability (L2)": "Investment Portfolio Management",
                    "Business Capability (L3)": "Portfolio, Mandate / Risk",
                    "Business Capability (L2) long name": "2.4 Product and Service Enabling / Investment Portfolio Management",
                    "Business Capability (L3) long name": "2.4.1 Product and Service Enabling / Investment Portfolio Management / Portfolio, Mandate / Risk",
                },
                {
                    "Business Capability (L1)": "Product and Service Enabling",
                    "Business Capability (L2)": "Product, Pricing / Billing",
                    "Business Capability (L3)": "Fees, Terms / Conditions",
                    "Business Capability (L2) long name": "2.5 Product and Service Enabling / Product, Pricing / Billing",
                    "Business Capability (L3) long name": "2.5.1 Product and Service Enabling / Product, Pricing / Billing / Fees, Terms / Conditions",
                },
            ]
        ),
        "E1-BCM": pd.DataFrame(
            [
                {
                    "Application Code": "APP-WIDE",
                    "Application Display Name": "Wide App",
                    "Application Name": "Wide App",
                    "BIAN L2": "2.4 - Product and Service Enabling/Investment Portfolio Management, 2.5 Product and Service Enabling / Product, Pricing / Billing",
                    "BIAN L3": "",
                },
                {
                    "Application Code": "APP-NARROW",
                    "Application Display Name": "Narrow App",
                    "Application Name": "Narrow App",
                    "BIAN L2": "",
                    "BIAN L3": "2.4.1 Product and Service Enabling / Investment Portfolio Management / Portfolio, Mandate / Risk",
                },
            ]
        ),
        "E2-BCM": _empty_mapping_sheet(),
        "E3-BCM": _empty_mapping_sheet(),
        "E4-BCM": _empty_mapping_sheet(),
    }


def sample_model() -> dict[str, pd.DataFrame]:
    model = build_model(sample_workbook(), DEFAULT_CONFIG)
    model["fact_incidents"] = pd.DataFrame(
        [
            {"application_code": "APP-WIDE", "year": 2025, "incident_type": 1, "incident_count": 4, "source_sheet": "Incidents", "source_row": 2},
            {"application_code": "APP-WIDE", "year": 2025, "incident_type": 2, "incident_count": 2, "source_sheet": "Incidents", "source_row": 3},
            {"application_code": "APP-NARROW", "year": 2025, "incident_type": 1, "incident_count": 1, "source_sheet": "Incidents", "source_row": 4},
        ],
        columns=["application_code", "year", "incident_type", "incident_count", "source_sheet", "source_row"],
    )
    return model


def empty_model() -> dict[str, pd.DataFrame]:
    return {
        "dim_business_capability": pd.DataFrame(
            columns=["code", "level", "label", "long_name", "parent_code", "path_l1", "path_l2", "path_l3", "path_l4", "path_l5"]
        ),
        "dim_application": pd.DataFrame(columns=["application_code", "application_name", "display_name", "entity_code"]),
        "dim_entity": pd.DataFrame(columns=["entity_code", "label"]),
        "bridge_application_capability": pd.DataFrame(
            columns=["application_code", "entity_code", "capability_code", "mapped_level", "source_sheet", "source_row"]
        ),
        "capability_closure": pd.DataFrame(columns=["ancestor_code", "descendant_code", "depth"]),
        "import_warnings": pd.DataFrame(columns=["severity", "source_sheet", "source_row", "message", "raw_value"]),
    }


def _empty_mapping_sheet() -> pd.DataFrame:
    return pd.DataFrame(columns=["Application Code", "Application Display Name", "Application Name", "BIAN L2", "BIAN L3"])
