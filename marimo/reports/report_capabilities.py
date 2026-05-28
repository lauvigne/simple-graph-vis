from __future__ import annotations

import pandas as pd


def capabilities_table(model: dict[str, pd.DataFrame]) -> pd.DataFrame:
    return model["dim_business_capability"].sort_values(["level", "code"])


def duplicate_capabilities(model: dict[str, pd.DataFrame]) -> pd.DataFrame:
    capabilities = model["dim_business_capability"]
    counts = capabilities.groupby("long_name").size().reset_index(name="count")
    return counts[counts["count"] > 1].sort_values("count", ascending=False)
