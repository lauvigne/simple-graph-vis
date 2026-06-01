from __future__ import annotations

import pandas as pd

from .coverage import covering_applications_map


def capability_sunburst(capabilities: pd.DataFrame):
    try:
        import plotly.express as px
        import plotly.graph_objects as go
    except ImportError:
        return "Plotly is not installed. Run `pip install -r requirements.txt`."

    frame = capabilities.copy()
    if frame.empty:
        return go.Figure().update_layout(title="No business capabilities loaded")
    frame["metric"] = 1
    height = _dynamic_height(len(frame), base=1100, per_item=6, minimum=1100, maximum=2600)
    fig = px.sunburst(
        frame,
        path=["path_l1", "path_l2", "path_l3"],
        values="metric",
        title="Business capabilities",
    )
    fig.update_layout(
        autosize=True,
        width=None,
        height=height,
        margin=dict(l=0, r=0, t=60, b=0),
        uniformtext=dict(minsize=10, mode="hide"),
    )
    return fig


def application_capability_sankey(model: dict[str, pd.DataFrame], capability_codes: list[str] | None = None, limit: int | None = None):
    try:
        import plotly.graph_objects as go
    except ImportError:
        return "Plotly is not installed. Run `pip install -r requirements.txt`."

    bridge = model["bridge_application_capability"].copy()
    if capability_codes:
        bridge = bridge[bridge["capability_code"].isin(capability_codes)]
    if limit is not None:
        bridge = bridge.head(limit)
    if bridge.empty:
        return go.Figure().update_layout(title="No application mappings loaded")
    capabilities = model["dim_business_capability"][["code", "label"]].rename(columns={"label": "capability_name"})
    applications = model["dim_application"][["application_code", "display_name", "entity_code"]].copy()
    entities = model["dim_entity"][["entity_code", "label"]].rename(columns={"label": "entity_name"})

    app_nodes = bridge[["application_code"]].drop_duplicates().merge(applications, on="application_code", how="left")
    app_nodes = app_nodes.merge(entities, on="entity_code", how="left")
    app_nodes["entity_name"] = app_nodes["entity_name"].fillna(app_nodes["entity_code"]).astype(str)
    app_nodes["display_name"] = app_nodes["display_name"].fillna("").astype(str)

    covering_map = covering_applications_map(model, application_codes=app_nodes["application_code"].dropna().astype(str).tolist())
    app_nodes = app_nodes.merge(covering_map, on="application_code", how="left")
    app_nodes["covering_applications"] = app_nodes["covering_applications"].apply(
        lambda value: value if isinstance(value, list) else []
    )
    app_nodes["application_label"] = app_nodes.apply(
        lambda row: _format_application_label(row["entity_name"], row["application_code"], row["display_name"]),
        axis=1,
    )
    app_nodes["application_tooltip"] = app_nodes.apply(
        lambda row: _format_application_tooltip(
            row["entity_name"], row["application_code"], row["display_name"], row["covering_applications"]
        ),
        axis=1,
    )

    cap_nodes = bridge[["capability_code"]].drop_duplicates().merge(capabilities, left_on="capability_code", right_on="code", how="left")
    cap_nodes["capability_name"] = cap_nodes["capability_name"].fillna("").astype(str)
    cap_nodes["capability_label"] = cap_nodes["code"].astype(str)
    cap_nodes["capability_tooltip"] = cap_nodes.apply(
        lambda row: _format_capability_tooltip(row["code"], row["capability_name"]),
        axis=1,
    )
    link_data = bridge.merge(app_nodes[["application_code", "application_label"]], on="application_code", how="left")
    link_data = link_data.merge(cap_nodes[["capability_code", "capability_label"]], on="capability_code", how="left")

    application_labels = list(dict.fromkeys(app_nodes["application_label"].astype(str)))
    capability_labels = list(dict.fromkeys(cap_nodes["capability_label"].astype(str)))
    labels = list(dict.fromkeys([*application_labels, *capability_labels]))
    index = {label: i for i, label in enumerate(labels)}
    app_count = app_nodes["application_label"].nunique()
    cap_count = cap_nodes["capability_label"].nunique()
    height = _dynamic_height(max(app_count, cap_count), base=1400, per_item=10, minimum=1400, maximum=12000)
    application_set = set(application_labels)
    capability_set = set(capability_labels)
    node_colors = [
        "rgba(31, 119, 180, 0.8)" if label in application_set else "rgba(44, 160, 44, 0.8)" if label in capability_set else "rgba(128, 128, 128, 0.8)"
        for label in labels
    ]
    fig = go.Figure(
        data=[
            go.Sankey(
                node={
                    "label": labels,
                    "color": node_colors,
                    "pad": 12,
                    "thickness": 12,
                    "line": {"width": 0.2, "color": "rgba(80, 80, 80, 0.2)"},
                },
                arrangement="snap",
                link={
                    "source": [index[value] for value in link_data["application_label"]],
                    "target": [index[value] for value in link_data["capability_label"]],
                    "value": [1] * len(link_data),
                },
            )
        ]
    )
    node_customdata = [
        app_nodes.loc[app_nodes["application_label"] == label, "application_tooltip"].iloc[0]
        if label in application_set
        else cap_nodes.loc[cap_nodes["capability_label"] == label, "capability_tooltip"].iloc[0]
        for label in labels
    ]
    fig.data[0].node.customdata = node_customdata
    fig.data[0].node.hovertemplate = "%{customdata}<extra></extra>"
    fig.update_layout(
        title="Application -> capability mappings",
        autosize=True,
        width=None,
        height=height,
        margin=dict(l=0, r=0, t=60, b=0),
    )
    return fig


def _format_application_label(entity_code: object, application_code: object, display_name: object) -> str:
    entity_text = str(entity_code or "").strip()
    application_text = str(application_code or "").strip()
    prefix = f"{entity_text}#" if entity_text else ""
    return f"{prefix}{application_text}"


def _format_application_tooltip(entity_code: object, application_code: object, display_name: object, covering_applications: list[str] | None = None) -> str:
    entity_text = str(entity_code or "").strip()
    application_text = str(application_code or "").strip()
    display_text = str(display_name or "").strip()
    parts = [f"{entity_text}#{application_text}" if entity_text else application_text]
    if display_text:
        parts.append(display_text)
    if covering_applications:
        parts.append("Couverte par: " + ", ".join(covering_applications))
    else:
        parts.append("Couverte par: aucune")
    return " - ".join(parts)


def _format_capability_tooltip(code: object, label: object) -> str:
    code_text = str(code or "").strip()
    label_text = str(label or "").strip()
    if code_text and label_text:
        return f"{code_text}#{label_text}"
    return code_text or label_text or ""


def _dynamic_height(count: int, base: int, per_item: int, minimum: int, maximum: int) -> int:
    return max(minimum, min(maximum, base + count * per_item))
