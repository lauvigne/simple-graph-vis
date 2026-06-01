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
    data = bridge.merge(capabilities, left_on="capability_code", right_on="code", how="left")
    labels = list(dict.fromkeys([*data["application_code"], *data["label"]]))
    index = {label: i for i, label in enumerate(labels)}
    app_count = data["application_code"].nunique()
    cap_count = data["label"].nunique()
    height = _dynamic_height(max(app_count, cap_count), base=1400, per_item=10, minimum=1400, maximum=12000)
    fig = go.Figure(
        data=[
            go.Sankey(
                node={
                    "label": labels,
                    "pad": 12,
                    "thickness": 10,
                    "line": {"width": 0.2, "color": "rgba(80, 80, 80, 0.2)"},
                },
                arrangement="snap",
                link={
                    "source": [index[value] for value in data["application_code"]],
                    "target": [index[value] for value in data["label"]],
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


def _dynamic_height(count: int, base: int, per_item: int, minimum: int, maximum: int) -> int:
    return max(minimum, min(maximum, base + count * per_item))
