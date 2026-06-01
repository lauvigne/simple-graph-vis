"""Reusable helpers for report-style Marimo notebooks.

This package contains aggregation and rendering helpers that are shared across
the notebooks in ``notebooks/reports/``. It intentionally stays in ``src``
because it is business/reporting logic, not a notebook entrypoint.
"""

from __future__ import annotations

import pandas as pd

from src.charts import application_capability_sankey, capability_sunburst
from src.coverage import candidate_details as _candidate_details_impl
from src.coverage import coverage_candidates as _coverage_candidates_impl
from src.coverage import covering_applications_map
from src.capability_picker import (
    capability_catalog,
    leaf_options,
    level1_options,
    level2_options,
    selected_leaf_labels as _selected_leaf_labels,
)
from src.treemap import treemap_data, treemap_figure


def capabilities_table(model: dict[str, pd.DataFrame]) -> pd.DataFrame:
    return model["dim_business_capability"].sort_values(["level", "code"])


def duplicate_capabilities(model: dict[str, pd.DataFrame]) -> pd.DataFrame:
    capabilities = model["dim_business_capability"]
    counts = capabilities.groupby("long_name").size().reset_index(name="count")
    return counts[counts["count"] > 1].sort_values("count", ascending=False)


def query_candidates(
    model: dict[str, pd.DataFrame],
    threshold: float,
    entity: str | None,
    scope_mode: str = "all",
) -> pd.DataFrame:
    return _coverage_candidates_impl(model, threshold=threshold, entity=entity or None, scope_mode=scope_mode)


def query_candidate_details(model: dict[str, pd.DataFrame], covered_app: str, covering_app: str) -> dict[str, pd.DataFrame]:
    return _candidate_details_impl(model, covered_app, covering_app)


def build_treemap_data(model: dict[str, pd.DataFrame], metric: str) -> pd.DataFrame:
    return treemap_data(model, metric)


def build_treemap_figure(frame: pd.DataFrame, metric: str):
    return treemap_figure(frame, metric)


def build_capability_sunburst(model: dict[str, pd.DataFrame]):
    return capability_sunburst(model["dim_business_capability"])


def build_mapping_sankey(model: dict[str, pd.DataFrame], capability_codes: list[str] | None = None):
    return application_capability_sankey(model, capability_codes=capability_codes)


def build_sankey(model: dict[str, pd.DataFrame], capability_codes: list[str] | None = None):
    return application_capability_sankey(model, capability_codes=capability_codes)


def build_capability_catalog(model: dict[str, pd.DataFrame]) -> pd.DataFrame:
    return capability_catalog(model)


def build_filtered_catalog(
    model: dict[str, pd.DataFrame],
    search: str = "",
    l1_code: str = "",
    l2_code: str = "",
) -> pd.DataFrame:
    catalog = capability_catalog(model)
    frame = catalog
    if search.strip():
        query = search.strip().lower()
        frame = frame[frame["search_blob"].str.contains(query, na=False)]
    if l1_code:
        frame = frame[frame["l1_code"] == l1_code]
    if l2_code:
        frame = frame[frame["l2_code"] == l2_code]
    return frame.reset_index(drop=True)


def build_level1_options(model: dict[str, pd.DataFrame], search: str = "") -> dict[str, str]:
    return level1_options(capability_catalog(model), search=search)


def build_level2_options(model: dict[str, pd.DataFrame], search: str = "", l1_code: str = "") -> dict[str, str]:
    return level2_options(capability_catalog(model), search=search, l1_code=l1_code)


def build_leaf_options(
    model: dict[str, pd.DataFrame],
    search: str = "",
    l1_code: str = "",
    l2_code: str = "",
) -> dict[str, str]:
    return leaf_options(capability_catalog(model), search=search, l1_code=l1_code, l2_code=l2_code)


def describe_selected_leaves(model: dict[str, pd.DataFrame], selected_codes: list[str]) -> list[str]:
    catalog = capability_catalog(model)
    return _selected_leaf_labels(catalog, selected_codes)


def covered_by_map(model: dict[str, pd.DataFrame], application_codes: list[str] | None = None) -> pd.DataFrame:
    return covering_applications_map(model, application_codes=application_codes)


__all__ = [
    "capabilities_table",
    "duplicate_capabilities",
    "query_candidates",
    "query_candidate_details",
    "build_treemap_data",
    "build_treemap_figure",
    "build_capability_sunburst",
    "build_mapping_sankey",
    "build_sankey",
    "build_capability_catalog",
    "build_filtered_catalog",
    "build_level1_options",
    "build_level2_options",
    "build_leaf_options",
    "describe_selected_leaves",
    "covered_by_map",
]
