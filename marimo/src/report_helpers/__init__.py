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
from src.sankey_hierarchy import hierarchical_application_sankey
from src.treemap import treemap_data, treemap_figure


def application_directory(model: dict[str, pd.DataFrame]) -> pd.DataFrame:
    applications = model.get("dim_application", pd.DataFrame()).copy()
    entities = model.get("dim_entity", pd.DataFrame()).copy()
    if applications.empty:
        return pd.DataFrame(
            columns=[
                "application_code",
                "entity_code",
                "entity_label",
                "application_name",
                "display_name",
                "application_ref",
                "application_detail",
                "selector_label",
            ]
        )

    for column in ["application_code", "application_name", "display_name", "entity_code"]:
        if column not in applications.columns:
            applications[column] = ""
        applications[column] = applications[column].fillna("").astype(str).str.strip()

    if entities.empty:
        entities = pd.DataFrame(columns=["entity_code", "label"])
    if "entity_code" not in entities.columns:
        entities["entity_code"] = ""
    if "label" not in entities.columns:
        entities["label"] = ""
    entities["entity_code"] = entities["entity_code"].fillna("").astype(str).str.strip()
    entities["entity_label"] = entities["label"].fillna("").astype(str).str.strip()
    entities.loc[entities["entity_label"] == "", "entity_label"] = entities.loc[entities["entity_label"] == "", "entity_code"]

    frame = applications.merge(
        entities[["entity_code", "entity_label"]].drop_duplicates(),
        on="entity_code",
        how="left",
    )
    frame["entity_label"] = frame["entity_label"].fillna("").astype(str).str.strip()
    frame.loc[frame["entity_label"] == "", "entity_label"] = frame.loc[frame["entity_label"] == "", "entity_code"]
    frame["application_name"] = frame["application_name"].fillna("").astype(str).str.strip()
    frame["display_name"] = frame["display_name"].fillna("").astype(str).str.strip()
    frame["application_ref"] = frame.apply(
        lambda row: _format_application_ref(row["entity_label"], row["application_code"]),
        axis=1,
    )
    frame["application_detail"] = frame.apply(
        lambda row: _format_application_detail(row["entity_label"], row["application_code"], row["display_name"], row["application_name"]),
        axis=1,
    )
    frame["selector_label"] = frame["application_detail"]
    frame = frame[
        [
            "application_code",
            "entity_code",
            "entity_label",
            "application_name",
            "display_name",
            "application_ref",
            "application_detail",
            "selector_label",
        ]
    ].drop_duplicates()
    return frame.sort_values(["entity_label", "application_code"]).reset_index(drop=True)


def application_options(model: dict[str, pd.DataFrame], application_codes: list[str] | None = None) -> dict[str, str]:
    frame = application_directory(model)
    if application_codes:
        frame = frame[frame["application_code"].isin(application_codes)]
    return {str(row["selector_label"]): str(row["application_code"]) for _, row in frame.iterrows() if str(row["application_code"]).strip()}


def coverage_candidates_display(
    model: dict[str, pd.DataFrame],
    threshold: float,
    entity: str | None,
    scope_mode: str = "all",
    limit: int = 5000,
) -> pd.DataFrame:
    candidates = _coverage_candidates_impl(
        model,
        threshold=threshold,
        entity=entity,
        scope_mode=scope_mode,
        limit=limit,
    )
    if candidates.empty:
        return pd.DataFrame(
            columns=[
                "application_code_covered",
                "entity_code_covered",
                "covered_entity_label",
                "covered_application_ref",
                "covered_application_detail",
                "application_code_covering",
                "entity_code_covering",
                "covering_entity_label",
                "covering_application_ref",
                "covering_application_detail",
                "overlap_count",
                "covered_count",
                "covering_count",
                "coverage",
                "type",
            ]
        )

    directory = application_directory(model)
    covered_directory = directory.rename(
        columns={
            "application_code": "application_code_covered",
            "entity_code": "entity_code_covered",
            "entity_label": "covered_entity_label",
            "application_name": "covered_application_name",
            "display_name": "covered_display_name",
            "application_ref": "covered_application_ref",
            "application_detail": "covered_application_detail",
            "selector_label": "covered_selector_label",
        }
    )
    covering_directory = directory.rename(
        columns={
            "application_code": "application_code_covering",
            "entity_code": "entity_code_covering",
            "entity_label": "covering_entity_label",
            "application_name": "covering_application_name",
            "display_name": "covering_display_name",
            "application_ref": "covering_application_ref",
            "application_detail": "covering_application_detail",
            "selector_label": "covering_selector_label",
        }
    )

    frame = candidates.merge(
        covered_directory,
        on=["application_code_covered", "entity_code_covered"],
        how="left",
    )
    frame = frame.merge(
        covering_directory,
        on=["application_code_covering", "entity_code_covering"],
        how="left",
    )
    frame = frame[
        [
            "application_code_covered",
            "entity_code_covered",
            "covered_entity_label",
            "covered_application_ref",
            "covered_application_detail",
            "application_code_covering",
            "entity_code_covering",
            "covering_entity_label",
            "covering_application_ref",
            "covering_application_detail",
            "overlap_count",
            "covered_count",
            "covering_count",
            "coverage",
            "type",
        ]
    ]
    return frame.sort_values(
        ["coverage", "application_code_covered", "application_code_covering"],
        ascending=[False, True, True],
    ).reset_index(drop=True)


def covering_applications_detail(model: dict[str, pd.DataFrame], application_code: str) -> pd.DataFrame:
    mapping = covering_applications_map(model, application_codes=[application_code])
    if mapping.empty:
        return pd.DataFrame(columns=["application_code", "application_ref", "application_detail"])

    covering_refs = mapping.loc[mapping["application_code"] == application_code, "covering_applications"]
    if covering_refs.empty:
        return pd.DataFrame(columns=["application_code", "application_ref", "application_detail"])

    refs = covering_refs.iloc[0]
    if not isinstance(refs, list):
        refs = [refs]

    directory = application_directory(model)
    lookup = directory.drop_duplicates("application_code").set_index("application_code")
    rows: list[dict[str, str]] = []
    for index, ref in enumerate(refs):
        app_code = str(ref).split("#", 1)[-1].strip()
        if not app_code:
            continue
        if app_code in lookup.index:
            record = lookup.loc[app_code]
            if isinstance(record, pd.DataFrame):
                record = record.iloc[0]
            rows.append(
                {
                    "application_code": app_code,
                    "application_ref": str(record.get("application_ref", app_code)),
                    "application_detail": str(record.get("application_detail", app_code)),
                    "_order": index,
                }
            )
        else:
            rows.append(
                {
                    "application_code": app_code,
                    "application_ref": app_code,
                    "application_detail": app_code,
                    "_order": index,
                }
            )

    if not rows:
        return pd.DataFrame(columns=["application_code", "application_ref", "application_detail"])
    return pd.DataFrame(rows).sort_values("_order").drop(columns=["_order"]).reset_index(drop=True)


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


def build_hierarchical_sankey(model: dict[str, pd.DataFrame], capability_codes: list[str] | None = None):
    return hierarchical_application_sankey(model, capability_codes=capability_codes)


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
    "application_directory",
    "application_options",
    "capabilities_table",
    "duplicate_capabilities",
    "coverage_candidates_display",
    "covering_applications_detail",
    "query_candidates",
    "query_candidate_details",
    "build_treemap_data",
    "build_treemap_figure",
    "build_capability_sunburst",
    "build_mapping_sankey",
    "build_sankey",
    "build_hierarchical_sankey",
    "build_capability_catalog",
    "build_filtered_catalog",
    "build_level1_options",
    "build_level2_options",
    "build_leaf_options",
    "describe_selected_leaves",
    "covered_by_map",
]


def _format_application_ref(entity_label: object, application_code: object) -> str:
    entity_text = str(entity_label or "").strip()
    application_text = str(application_code or "").strip()
    if entity_text and application_text:
        return f"{entity_text}#{application_text}"
    return application_text or entity_text or ""


def _format_application_detail(
    entity_label: object,
    application_code: object,
    display_name: object,
    application_name: object,
) -> str:
    base = _format_application_ref(entity_label, application_code)
    name_text = str(display_name or "").strip() or str(application_name or "").strip()
    if base and name_text:
        return f"{base} - {name_text}"
    return base or name_text or ""
