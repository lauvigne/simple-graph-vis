from __future__ import annotations

from collections import defaultdict

import pandas as pd


TREEMAP_PATH_COLUMNS = ["path_l1", "path_l2", "path_l3", "path_l4", "path_l5"]


def treemap_data(model: dict[str, pd.DataFrame], metric: str) -> pd.DataFrame:
    capabilities = _capabilities_frame(model)
    if capabilities.empty:
        return _empty_treemap_frame()

    metric = metric.lower().strip()
    if metric == "applications":
        metric_frame = _applications_metric(model)
        metric_label = "Nombre d'applications"
    elif metric == "incidents":
        metric_frame = _incidents_metric(model)
        metric_label = "Nombre d'incidents"
    else:
        raise ValueError(f"Unsupported treemap metric: {metric}")

    frame = capabilities.merge(metric_frame, on="code", how="left")
    frame["metric_value"] = frame["metric_value"].fillna(0).astype(float)
    frame["tree_weight"] = _compute_tree_weights(frame)
    frame["metric_label"] = metric_label
    frame["display_label"] = frame["code"].astype(str)
    return frame.sort_values(["level", "path_l1", "path_l2", "path_l3", "code"], na_position="last")


def treemap_figure(frame: pd.DataFrame, metric: str):
    try:
        import plotly.graph_objects as go
    except ImportError:
        return "Plotly is not installed. Run `pip install -r requirements.txt`."

    if frame.empty:
        return go.Figure().update_layout(title=f"Treemap {metric}: no business capabilities loaded")

    customdata = frame[["metric_value", "long_name", "level"]].astype(object).to_numpy()
    parents = frame["parent_code"].fillna("").astype(str)
    labels = frame["display_label"].astype(str)
    hovertemplate = (
        "<b>%{label}</b><br>"
        "Chemin: %{customdata[1]}<br>"
        "Valeur directe: %{customdata[0]}<br>"
        "Niveau: %{customdata[2]}<br>"
        "Poids affiché: %{value}<extra></extra>"
    )
    fig = go.Figure(
        go.Treemap(
            ids=frame["code"].astype(str),
            labels=labels,
            parents=parents,
            values=frame["tree_weight"],
            customdata=customdata,
            branchvalues="total",
            hovertemplate=hovertemplate,
            textinfo="label",
        )
    )
    title = frame["metric_label"].iloc[0] if "metric_label" in frame.columns and not frame.empty else metric
    fig.update_layout(
        title=f"Treemap des business capabilities - {title}",
        height=900,
        margin=dict(l=10, r=10, t=60, b=10),
    )
    return fig


def _applications_metric(model: dict[str, pd.DataFrame]) -> pd.DataFrame:
    bridge = model.get("bridge_application_capability", pd.DataFrame())
    if bridge.empty:
        return pd.DataFrame(columns=["code", "metric_value"])
    counts = (
        bridge.groupby("capability_code")["application_code"]
        .nunique()
        .reset_index(name="metric_value")
        .rename(columns={"capability_code": "code"})
    )
    return counts


def _incidents_metric(model: dict[str, pd.DataFrame]) -> pd.DataFrame:
    incidents = model.get("fact_incidents", pd.DataFrame())
    if incidents.empty:
        return pd.DataFrame(columns=["code", "metric_value"])
    app_incidents = (
        incidents.groupby("application_code")["incident_count"]
        .sum()
        .reset_index(name="incident_total")
    )
    bridge = model.get("bridge_application_capability", pd.DataFrame())
    if bridge.empty:
        return pd.DataFrame(columns=["code", "metric_value"])
    per_capability = (
        bridge.merge(app_incidents, on="application_code", how="inner")
        .groupby("capability_code")["incident_total"]
        .sum()
        .reset_index(name="metric_value")
        .rename(columns={"capability_code": "code"})
    )
    return per_capability


def _capabilities_frame(model: dict[str, pd.DataFrame]) -> pd.DataFrame:
    capabilities = model.get("dim_business_capability", pd.DataFrame()).copy()
    if capabilities.empty:
        return _empty_treemap_frame()
    for column in TREEMAP_PATH_COLUMNS:
        if column not in capabilities.columns:
            capabilities[column] = ""
    for column in ("code", "parent_code", "label", "long_name", "level"):
        if column not in capabilities.columns:
            capabilities[column] = ""
    capabilities = capabilities[["code", "parent_code", "label", "long_name", "level", *TREEMAP_PATH_COLUMNS]]
    capabilities["code"] = capabilities["code"].astype(str)
    capabilities["parent_code"] = capabilities["parent_code"].astype(str)
    capabilities["label"] = capabilities["label"].astype(str)
    capabilities["long_name"] = capabilities["long_name"].astype(str)
    capabilities["level"] = pd.to_numeric(capabilities["level"], errors="coerce").fillna(0).astype(int)
    return capabilities


def _compute_tree_weights(frame: pd.DataFrame) -> pd.Series:
    by_parent: dict[str, list[str]] = defaultdict(list)
    for code, parent_code in frame[["code", "parent_code"]].itertuples(index=False):
        if parent_code:
            by_parent[str(parent_code)].append(str(code))

    metric_by_code = dict(zip(frame["code"].astype(str), frame["metric_value"].astype(float)))
    weight_by_code: dict[str, float] = {}

    def _weight(code: str) -> float:
        if code in weight_by_code:
            return weight_by_code[code]
        children = by_parent.get(code, [])
        weight = float(metric_by_code.get(code, 0.0)) + sum(_weight(child) for child in children)
        weight_by_code[code] = weight
        return weight

    for code in frame["code"].astype(str):
        _weight(code)
    return frame["code"].astype(str).map(weight_by_code).fillna(0.0)


def _empty_treemap_frame() -> pd.DataFrame:
    return pd.DataFrame(
        columns=[
            "code",
            "parent_code",
            "label",
            "long_name",
            "level",
            *TREEMAP_PATH_COLUMNS,
            "metric_value",
            "tree_weight",
            "metric_label",
            "display_label",
        ]
    )
