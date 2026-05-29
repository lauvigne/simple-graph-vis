from __future__ import annotations

import pandas as pd

from src.treemap import treemap_data, treemap_figure


def build_treemap_data(model: dict[str, pd.DataFrame], metric: str) -> pd.DataFrame:
    return treemap_data(model, metric)


def build_treemap_figure(frame: pd.DataFrame, metric: str):
    return treemap_figure(frame, metric)
