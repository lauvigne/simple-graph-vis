from __future__ import annotations

from collections import defaultdict
from functools import lru_cache

import pandas as pd


TREEMAP_COLUMNS = [
    "id",
    "code",
    "parent_id",
    "parent_code",
    "label",
    "display_label",
    "long_name",
    "level",
    "kind",
    "entity_code",
    "application_code",
    "metric_value",
    "tree_weight",
    "hover_label",
]


def treemap_data(model: dict[str, pd.DataFrame], metric: str) -> pd.DataFrame:
    capabilities = _capability_frame(model)
    applications = _application_frame(model, metric)
    if capabilities.empty or applications.empty:
        return _empty_treemap_frame()

    nodes = _build_nodes(capabilities, applications)
    if not nodes:
        return _empty_treemap_frame()

    frame = pd.DataFrame(nodes, columns=TREEMAP_COLUMNS)
    if frame.empty:
        return _empty_treemap_frame()

    tree_weights = _compute_tree_weights(frame)
    frame["tree_weight"] = frame["id"].map(tree_weights).fillna(frame["metric_value"]).astype(float)
    frame["metric_value"] = frame["metric_value"].fillna(0).astype(float)
    frame["display_label"] = frame["display_label"].fillna(frame["label"]).astype(str)
    frame["hover_label"] = frame["hover_label"].fillna(frame["display_label"]).astype(str)
    return frame.sort_values(["kind", "level", "code", "application_code"], na_position="last").reset_index(drop=True)


def treemap_figure(frame: pd.DataFrame, metric: str):
    try:
        import plotly.graph_objects as go
    except ImportError:
        return "Plotly is not installed. Run `pip install -r requirements.txt`."

    if frame.empty:
        return go.Figure().update_layout(title=f"No data available for {metric}")

    color_values = pd.to_numeric(frame["tree_weight"], errors="coerce").fillna(0).astype(float)
    color_min = float(color_values.min()) if not color_values.empty else 0.0
    color_max = float(color_values.max()) if not color_values.empty else 1.0
    if color_max <= color_min:
        color_max = color_min + 1.0
    color_scale = [
        [0.0, "#2ca02c"],
        [0.5, "#4fba74"],
        [1.0, "#1f77b4"],
    ]

    fig = go.Figure(
        go.Treemap(
            ids=frame["id"],
            labels=frame["display_label"],
            parents=frame["parent_id"].fillna(""),
            values=frame["tree_weight"],
            branchvalues="total",
            maxdepth=3,
            sort=False,
            marker=dict(
                colors=color_values,
                cmin=color_min,
                cmax=color_max,
                colorscale=color_scale,
                showscale=True,
                colorbar=dict(
                    title="Poids",
                    thickness=16,
                    len=0.75,
                    tickformat=",.0f",
                ),
                line=dict(width=0.3, color="rgba(90, 90, 90, 0.3)"),
            ),
            customdata=frame[["kind", "level", "metric_value", "tree_weight", "hover_label"]],
            hovertemplate=(
                "<b>%{customdata[4]}</b><br>"
                "Type: %{customdata[0]}<br>"
                "Niveau: %{customdata[1]}<br>"
                "Valeur directe: %{customdata[2]:,.0f}<br>"
                "Poids cumul&eacute;: %{customdata[3]:,.0f}"
                "<extra></extra>"
            ),
        )
    )
    fig.update_layout(
        title=f"Business capabilities -> applications ({metric})",
        autosize=True,
        width=None,
        height=900,
        margin=dict(l=0, r=0, t=60, b=0),
    )
    return fig


def _capability_frame(model: dict[str, pd.DataFrame]) -> pd.DataFrame:
    capabilities = model.get("dim_business_capability", pd.DataFrame()).copy()
    required = {"code", "level", "label", "long_name", "parent_code", "path_l1", "path_l2", "path_l3", "path_l4", "path_l5"}
    for column in required:
        if column not in capabilities.columns:
            capabilities[column] = ""
    if capabilities.empty:
        return capabilities
    capabilities["code"] = capabilities["code"].fillna("").astype(str)
    capabilities["parent_code"] = capabilities["parent_code"].fillna("").astype(str)
    capabilities["label"] = capabilities["label"].fillna("").astype(str)
    capabilities["long_name"] = capabilities["long_name"].fillna("").astype(str)
    capabilities["level"] = pd.to_numeric(capabilities["level"], errors="coerce").fillna(0).astype(int)
    return capabilities[capabilities["code"].str.strip() != ""].reset_index(drop=True)


def _application_frame(model: dict[str, pd.DataFrame], metric: str) -> pd.DataFrame:
    bridge = model.get("bridge_application_capability", pd.DataFrame()).copy()
    if bridge.empty:
        return pd.DataFrame(columns=["application_code", "entity_code", "application_name", "display_name", "capability_code", "metric_value"])

    applications = model.get("dim_application", pd.DataFrame())[
        ["application_code", "application_name", "display_name", "entity_code"]
    ].copy()
    entities = model.get("dim_entity", pd.DataFrame())[["entity_code", "label"]].rename(columns={"label": "entity_label"})
    applications = applications.merge(entities, on="entity_code", how="left")
    applications["entity_label"] = applications["entity_label"].fillna(applications["entity_code"]).astype(str)
    applications["application_name"] = applications["application_name"].fillna("").astype(str)
    applications["display_name"] = applications["display_name"].fillna("").astype(str)

    if metric == "incidents":
        incidents = model.get("fact_incidents", pd.DataFrame()).copy()
        if incidents.empty:
            return pd.DataFrame(columns=["application_code", "entity_code", "application_name", "display_name", "capability_code", "metric_value"])
        incidents["incident_count"] = pd.to_numeric(incidents["incident_count"], errors="coerce").fillna(0)
        incident_totals = incidents.groupby("application_code", as_index=False)["incident_count"].sum()
        incident_totals = incident_totals.rename(columns={"incident_count": "metric_value"})
        applications = applications.merge(incident_totals, on="application_code", how="inner")
    else:
        applications["metric_value"] = 1.0

    frame = bridge.merge(applications, on=["application_code", "entity_code"], how="inner")
    frame["metric_value"] = pd.to_numeric(frame["metric_value"], errors="coerce").fillna(0)
    frame["capability_code"] = frame["capability_code"].fillna("").astype(str)
    frame = frame[frame["capability_code"].str.strip() != ""]
    return frame[["application_code", "entity_code", "entity_label", "application_name", "display_name", "capability_code", "metric_value"]].drop_duplicates(
        subset=["application_code", "entity_code", "capability_code"]
    )


def _build_nodes(capabilities: pd.DataFrame, applications: pd.DataFrame) -> list[dict[str, object]]:
    capability_rows = capabilities.to_dict(orient="records")
    app_rows = applications.to_dict(orient="records")
    rows: list[dict[str, object]] = []
    capability_by_code = {str(row["code"]): row for row in capability_rows}

    app_counter = defaultdict(int)
    for row in app_rows:
        capability_code = str(row["capability_code"] or "").strip()
        if capability_code not in capability_by_code:
            continue
        parent = capability_by_code[capability_code]
        if int(parent.get("level") or 0) <= 2:
            continue
        app_counter[capability_code] += 1
        app_index = app_counter[capability_code]
        app_id = f"app::{capability_code}::{row['entity_code']}::{row['application_code']}::{app_index}"
        app_display_label = _format_application_label(row["entity_label"], row["application_code"])
        app_hover_label = _format_application_tooltip(
            row["entity_label"],
            row["application_code"],
            row["application_name"],
            row["display_name"],
        )
        rows.append(
            {
                "id": app_id,
                "code": str(row["application_code"]),
                "parent_id": f"cap::{capability_code}",
                "parent_code": capability_code,
                "label": app_display_label,
                "display_label": app_display_label,
                "long_name": str(row["application_name"] or row["display_name"] or ""),
                "level": int(parent["level"]) + 1 if str(parent.get("level") or "").isdigit() else 4,
                "kind": "application",
                "entity_code": str(row["entity_code"]),
                "application_code": str(row["application_code"]),
                "metric_value": float(row["metric_value"]),
                "tree_weight": float(row["metric_value"]),
                "hover_label": app_hover_label,
            }
        )

    for code, row in sorted(capability_by_code.items(), key=lambda item: (int(item[1]["level"]), item[0])):
        parent_code = str(row.get("parent_code") or "").strip()
        rows.append(
            {
                "id": f"cap::{code}",
                "code": code,
                "parent_id": f"cap::{parent_code}" if parent_code else "",
                "parent_code": parent_code,
                "label": code,
                "display_label": code,
                "long_name": str(row.get("long_name") or ""),
                "level": int(row.get("level") or 0),
                "kind": "capability",
                "entity_code": "",
                "application_code": "",
                "metric_value": 0.0,
                "tree_weight": 0.0,
                "hover_label": _format_capability_tooltip(code, row.get("long_name") or row.get("label") or ""),
            }
        )

    return rows


def _compute_tree_weights(frame: pd.DataFrame) -> dict[str, float]:
    children: dict[str, list[str]] = defaultdict(list)
    metrics = dict(zip(frame["id"], pd.to_numeric(frame["metric_value"], errors="coerce").fillna(0).astype(float)))
    for row in frame.itertuples(index=False):
        parent_id = str(getattr(row, "parent_id") or "").strip()
        if parent_id:
            children[parent_id].append(str(getattr(row, "id")))
    for child_ids in children.values():
        child_ids.sort()

    @lru_cache(maxsize=None)
    def weight(node_id: str) -> float:
        total = float(metrics.get(node_id, 0.0))
        for child_id in children.get(node_id, []):
            total += weight(child_id)
        return float(total)

    return {node_id: weight(node_id) for node_id in metrics}


def _format_application_label(entity_label: object, application_code: object) -> str:
    entity_text = str(entity_label or "").strip()
    application_text = str(application_code or "").strip()
    if entity_text and application_text:
        return f"{entity_text}#{application_text}"
    return application_text or entity_text or ""


def _format_application_tooltip(entity_label: object, application_code: object, application_name: object, display_name: object) -> str:
    entity_text = str(entity_label or "").strip()
    application_text = str(application_code or "").strip()
    name_text = str(application_name or display_name or "").strip()
    prefix = f"{entity_text}#{application_text}" if entity_text else application_text
    if name_text:
        return f"{prefix} - {name_text}".strip()
    return prefix


def _format_capability_tooltip(code: object, long_name: object) -> str:
    code_text = str(code or "").strip()
    long_name_text = str(long_name or "").strip()
    if code_text and long_name_text:
        return f"{code_text}#{long_name_text}"
    return code_text or long_name_text or ""


def _empty_treemap_frame() -> pd.DataFrame:
    return pd.DataFrame(columns=TREEMAP_COLUMNS)
