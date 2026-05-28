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
    fig = px.sunburst(
        frame,
        path=["path_l1", "path_l2", "path_l3"],
        values="metric",
        title="Business capabilities",
    )
    fig.update_layout(height=900, margin=dict(l=10, r=10, t=60, b=10), uniformtext=dict(minsize=10, mode="hide"))
    return fig


def application_capability_sankey(model: dict[str, pd.DataFrame], limit: int = 200):
    try:
        import plotly.graph_objects as go
    except ImportError:
        return "Plotly is not installed. Run `pip install -r requirements.txt`."

    bridge = model["bridge_application_capability"].head(limit)
    if bridge.empty:
        return go.Figure().update_layout(title="No application mappings loaded")
    capabilities = model["dim_business_capability"][["code", "label"]]
    data = bridge.merge(capabilities, left_on="capability_code", right_on="code", how="left")
    labels = list(dict.fromkeys([*data["application_code"], *data["label"]]))
    index = {label: i for i, label in enumerate(labels)}
    fig = go.Figure(
        data=[
            go.Sankey(
                node={"label": labels},
                link={
                    "source": [index[value] for value in data["application_code"]],
                    "target": [index[value] for value in data["label"]],
                    "value": [1] * len(data),
                },
            )
        ]
    )
    fig.update_layout(title="Application -> capability mappings", height=900, margin=dict(l=10, r=10, t=60, b=10))
    return fig
