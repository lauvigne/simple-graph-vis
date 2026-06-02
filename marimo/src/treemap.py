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
    "normalized_metric_value",
    "application_count",
    "incident_total",
    "tree_weight",
    "hover_label",
]


def treemap_data(
    model: dict[str, pd.DataFrame],
    metric: str,
    entity_code: str | None = None,
    incident_years: list[int] | None = None,
    incident_types: list[int] | None = None,
    normalize_incidents: bool = False,
) -> pd.DataFrame:
    capabilities = _capability_frame(model)
    applications = _application_frame(
        model,
        metric,
        entity_code=entity_code,
        incident_years=incident_years,
        incident_types=incident_types,
    )
    if capabilities.empty or applications.empty:
        return _empty_treemap_frame()

    capability_ratios = _capability_incident_ratios(applications) if metric == "incidents" and normalize_incidents else {}
    nodes = _build_nodes(capabilities, applications, capability_ratios=capability_ratios)
    if not nodes:
        return _empty_treemap_frame()

    frame = pd.DataFrame(nodes, columns=TREEMAP_COLUMNS)
    if frame.empty:
        return _empty_treemap_frame()

    tree_weights = _compute_tree_weights(frame)
    frame["tree_weight"] = frame["id"].map(tree_weights).fillna(frame["metric_value"]).astype(float)
    frame["metric_value"] = frame["metric_value"].fillna(0).astype(float)
    frame["normalized_metric_value"] = pd.to_numeric(frame["normalized_metric_value"], errors="coerce").fillna(0).astype(float)
    frame["application_count"] = pd.to_numeric(frame["application_count"], errors="coerce").fillna(0).astype(float)
    frame["incident_total"] = pd.to_numeric(frame["incident_total"], errors="coerce").fillna(0).astype(float)
    frame["display_label"] = frame.apply(_format_display_label, axis=1)
    frame["hover_label"] = frame["hover_label"].fillna(frame["display_label"]).astype(str)
    return frame.sort_values(["kind", "level", "code", "application_code"], na_position="last").reset_index(drop=True)


def treemap_figure(frame: pd.DataFrame, metric: str, normalize_incidents: bool = False):
    try:
        import plotly.graph_objects as go
    except ImportError:
        return "Plotly is not installed. Run `pip install -r requirements.txt`."

    if frame.empty:
        return go.Figure().update_layout(title=f"No data available for {metric}")

    color_column = "normalized_metric_value" if metric == "incidents" and normalize_incidents else "tree_weight"
    level_3_values = pd.to_numeric(frame.loc[frame["level"] == 3, color_column], errors="coerce").fillna(0).astype(float)
    level_3_min = float(level_3_values.min()) if not level_3_values.empty else 0.0
    level_3_max = float(level_3_values.max()) if not level_3_values.empty else 1.0
    if level_3_max <= level_3_min:
        level_3_max = level_3_min + 1.0

    colors: list[str] = []
    for row in frame.itertuples(index=False):
        level = int(getattr(row, "level", 0) or 0)
        kind = str(getattr(row, "kind", "") or "")
        weight = float(getattr(row, color_column, 0.0) or 0.0)
        if level == 3:
            colors.append(_blend_hex_color("#2ca02c", "#1f77b4", (weight - level_3_min) / (level_3_max - level_3_min)))
        elif kind == "capability":
            if level <= 1:
                colors.append("#dff0df")
            elif level == 2:
                colors.append("#bfe6bf")
            else:
                colors.append("#f0f0f0")
        else:
            colors.append("#d9e6f2")

    normalize_extra = ""
    if metric == "incidents" and normalize_incidents:
        normalize_extra = (
            "<br>Incidents/applications: %{customdata[5]:,.2f}<br>"
            "Applications distinctes: %{customdata[6]:,.0f}<br>"
            "Incidents totaux: %{customdata[7]:,.0f}"
        )

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
                colors=colors,
                line=dict(width=0.3, color="rgba(90, 90, 90, 0.3)"),
            ),
            customdata=frame[
                [
                    "kind",
                    "level",
                    "metric_value",
                    "tree_weight",
                    "hover_label",
                    "normalized_metric_value",
                    "application_count",
                    "incident_total",
                ]
            ],
            hovertemplate=(
                "<b>%{customdata[4]}</b><br>"
                "Type: %{customdata[0]}<br>"
                "Niveau: %{customdata[1]}<br>"
                "Valeur directe: %{customdata[2]:,.0f}<br>"
                "Poids cumul&eacute;: %{customdata[3]:,.0f}"
                + normalize_extra
                + "<extra></extra>"
            ),
        )
    )
    title_suffix = " / application" if metric == "incidents" and normalize_incidents else ""
    fig.update_layout(
        title=f"Business capabilities -> applications ({metric}{title_suffix})",
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


def _application_frame(
    model: dict[str, pd.DataFrame],
    metric: str,
    entity_code: str | None = None,
    incident_years: list[int] | None = None,
    incident_types: list[int] | None = None,
) -> pd.DataFrame:
    bridge = model.get("bridge_application_capability", pd.DataFrame()).copy()
    if bridge.empty:
        return pd.DataFrame(columns=["application_code", "entity_code", "application_name", "display_name", "capability_code", "metric_value"])

    applications = model.get("dim_application", pd.DataFrame())[["application_code", "application_name", "display_name", "entity_code"]].copy()
    entities = model.get("dim_entity", pd.DataFrame())[["entity_code", "label"]].rename(columns={"label": "entity_label"})
    applications = applications.merge(entities, on="entity_code", how="left")
    applications["entity_label"] = applications["entity_label"].fillna(applications["entity_code"]).astype(str)
    applications["application_name"] = applications["application_name"].fillna("").astype(str)
    applications["display_name"] = applications["display_name"].fillna("").astype(str)

    if metric == "incidents":
        incidents = model.get("fact_incidents", pd.DataFrame()).copy()
        if incidents.empty:
            return pd.DataFrame(columns=["application_code", "entity_code", "application_name", "display_name", "capability_code", "metric_value"])
        if incident_years is not None:
            incidents = incidents[incidents["year"].isin(incident_years)]
        if incident_types is not None:
            incidents = incidents[incidents["incident_type"].isin(incident_types)]
        if incidents.empty:
            return pd.DataFrame(columns=["application_code", "entity_code", "application_name", "display_name", "capability_code", "metric_value"])
        incidents["incident_count"] = pd.to_numeric(incidents["incident_count"], errors="coerce").fillna(0)
        incident_totals = incidents.groupby("application_code", as_index=False)["incident_count"].sum()
        incident_totals = incident_totals.rename(columns={"incident_count": "metric_value"})
        applications = applications.merge(incident_totals, on="application_code", how="inner")
    else:
        applications["metric_value"] = 1.0

    frame = bridge.merge(applications, on=["application_code", "entity_code"], how="inner")
    if entity_code:
        frame = frame[frame["entity_code"] == entity_code]
    frame["metric_value"] = pd.to_numeric(frame["metric_value"], errors="coerce").fillna(0)
    frame["capability_code"] = frame["capability_code"].fillna("").astype(str)
    frame = frame[frame["capability_code"].str.strip() != ""]
    return frame[["application_code", "entity_code", "entity_label", "application_name", "display_name", "capability_code", "metric_value"]].drop_duplicates(
        subset=["application_code", "entity_code", "capability_code"]
    )


def _capability_incident_ratios(applications: pd.DataFrame) -> dict[str, dict[str, float]]:
    if applications.empty:
        return {}
    capability_totals = applications.groupby("capability_code", as_index=False).agg(
        incident_total=("metric_value", "sum"),
        application_count=("application_code", "nunique"),
    )
    capability_totals["metric_value"] = capability_totals.apply(
        lambda row: float(row["incident_total"]) / float(row["application_count"]) if float(row["application_count"]) else 0.0,
        axis=1,
    )
    return {
        str(row["capability_code"]): {
            "metric_value": float(row["metric_value"]),
            "incident_total": float(row["incident_total"]),
            "application_count": float(row["application_count"]),
        }
        for _, row in capability_totals.iterrows()
    }


def _build_nodes(
    capabilities: pd.DataFrame,
    applications: pd.DataFrame,
    capability_ratios: dict[str, dict[str, float]] | None = None,
) -> list[dict[str, object]]:
    capability_rows = capabilities.to_dict(orient="records")
    app_rows = applications.to_dict(orient="records")
    rows: list[dict[str, object]] = []
    capability_by_code = {str(row["code"]): row for row in capability_rows}
    capability_ratios = capability_ratios or {}

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
                "normalized_metric_value": float(row["metric_value"]),
                "application_count": 1.0,
                "incident_total": float(row["metric_value"]),
                "tree_weight": float(row["metric_value"]),
                "hover_label": app_hover_label,
            }
        )

    for code, row in sorted(capability_by_code.items(), key=lambda item: (int(item[1]["level"]), item[0])):
        parent_code = str(row.get("parent_code") or "").strip()
        ratio = capability_ratios.get(code, {})
        level = int(row.get("level") or 0)
        long_name = str(row.get("long_name") or row.get("label") or "").strip()
        rows.append(
            {
                "id": f"cap::{code}",
                "code": code,
                "parent_id": f"cap::{parent_code}" if parent_code else "",
                "parent_code": parent_code,
                "label": code,
                "display_label": code,
                "long_name": long_name,
                "level": level,
                "kind": "capability",
                "entity_code": "",
                "application_code": "",
                "metric_value": float(ratio.get("metric_value", 0.0)),
                "normalized_metric_value": float(ratio.get("metric_value", 0.0)),
                "application_count": float(ratio.get("application_count", 0.0)),
                "incident_total": float(ratio.get("incident_total", 0.0)),
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


def _format_display_label(row: pd.Series) -> str:
    kind = str(row.get("kind") or "").strip()
    code_text = str(row.get("code") or "").strip()
    long_name_text = str(row.get("long_name") or "").strip()
    level = int(row.get("level") or 0)
    tree_weight = float(row.get("tree_weight") or 0.0)
    if kind != "capability":
        return str(row.get("display_label") or row.get("label") or code_text).strip() or code_text
    if kind == "capability" and level == 3 and long_name_text:
        label = f"{code_text} - {long_name_text}"
        if tree_weight >= 2.0 or len(label) <= 72:
            return label
    return code_text


def _empty_treemap_frame() -> pd.DataFrame:
    return pd.DataFrame(columns=TREEMAP_COLUMNS)


def _blend_hex_color(start: str, end: str, ratio: float) -> str:
    ratio = max(0.0, min(1.0, float(ratio)))

    def _parse_hex(value: str) -> tuple[int, int, int]:
        value = value.lstrip("#")
        return tuple(int(value[index : index + 2], 16) for index in (0, 2, 4))

    start_rgb = _parse_hex(start)
    end_rgb = _parse_hex(end)
    blended = tuple(
        int(round(start_channel + (end_channel - start_channel) * ratio))
        for start_channel, end_channel in zip(start_rgb, end_rgb, strict=True)
    )
    return "#{:02x}{:02x}{:02x}".format(*blended)
