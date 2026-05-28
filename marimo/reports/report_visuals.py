from __future__ import annotations

import pandas as pd

from src.charts import application_capability_sankey, capability_sunburst


def build_capability_sunburst(model: dict[str, pd.DataFrame]):
    return capability_sunburst(model["dim_business_capability"])


def build_mapping_sankey(model: dict[str, pd.DataFrame]):
    return application_capability_sankey(model)
