from __future__ import annotations

import pandas as pd


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


def application_capability_sankey(model: dict[str, pd.DataFrame], limit: int | None = None):
    try:
        import plotly.graph_objects as go
    except ImportError:
        return "Plotly is not installed. Run `pip install -r requirements.txt`."

    bridge = model["bridge_application_capability"].copy()
    if limit is not None:
        bridge = bridge.head(limit)
    if bridge.empty:
        return go.Figure().update_layout(title="No application mappings loaded")
    capabilities = model["dim_business_capability"][["code", "label"]]
    applications = model["dim_application"][["application_code", "display_name", "entity_code"]].copy()
    entities = model["dim_entity"][["entity_code", "label"]].copy()
    data = bridge.merge(applications, on="application_code", how="left").merge(entities, on="entity_code", how="left", suffixes=("", "_entity"))
    data = data.merge(capabilities, left_on="capability_code", right_on="code", how="left", suffixes=("", "_capability"))
    data["application_label"] = data.apply(
        lambda row: _format_application_label(row["entity_code"], row["application_code"], row["display_name"]), axis=1
    )
    data["capability_label"] = data.apply(lambda row: _format_capability_label(row["code"], row["label"]), axis=1)
    labels = list(dict.fromkeys([*data["application_label"], *data["capability_label"]]))
    index = {label: i for i, label in enumerate(labels)}
    app_count = data["application_label"].nunique()
    cap_count = data["capability_label"].nunique()
    height = _dynamic_height(max(app_count, cap_count), base=1400, per_item=10, minimum=1400, maximum=12000)
    node_colors = []
    for label in labels:
        if "#" in label:
            node_colors.append("rgba(31, 119, 180, 0.8)")
        else:
            node_colors.append("rgba(44, 160, 44, 0.8)")
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
                    "source": [index[value] for value in data["application_label"]],
                    "target": [index[value] for value in data["capability_label"]],
                    "value": [1] * len(data),
                },
            )
        ]
    )
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
    display_text = str(display_name or "").strip()
    prefix = f"{entity_text}#" if entity_text else ""
    suffix = f" - {display_text}" if display_text and display_text != application_text else ""
    return f"{prefix}{application_text}{suffix}"


def _format_capability_label(code: object, label: object) -> str:
    code_text = str(code or "").strip()
    label_text = str(label or "").strip()
    if code_text and label_text:
        return f"{code_text}#{label_text}"
    return code_text or label_text or ""


def _dynamic_height(count: int, base: int, per_item: int, minimum: int, maximum: int) -> int:
    return max(minimum, min(maximum, base + count * per_item))
