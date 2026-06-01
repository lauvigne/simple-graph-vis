from __future__ import annotations

import pandas as pd


def hierarchical_application_sankey(model: dict[str, pd.DataFrame], capability_codes: list[str] | None = None):
    try:
        import plotly.graph_objects as go
    except ImportError:
        return "Plotly is not installed. Run `pip install -r requirements.txt`."

    links = _build_hierarchical_links(model, capability_codes=capability_codes)
    if links.empty:
        return go.Figure().update_layout(title="No hierarchical application mappings loaded")

    nodes = _build_nodes(model, links)
    if nodes.empty:
        return go.Figure().update_layout(title="No hierarchical application mappings loaded")

    labels = nodes["label"].tolist()
    index = {label: idx for idx, label in enumerate(labels)}
    node_colors = nodes["kind"].map(
        {
            "entity": "rgba(150, 150, 150, 0.78)",
            "application": "rgba(31, 119, 180, 0.82)",
            "capability_l3": "rgba(44, 160, 44, 0.82)",
            "capability_l2": "rgba(40, 120, 40, 0.88)",
        }
    ).fillna("rgba(128, 128, 128, 0.78)")

    link_colors = links["kind"].map(
        {
            "entity_application": "rgba(31, 119, 180, 0.22)",
            "application_capability_l3": "rgba(44, 160, 44, 0.24)",
            "capability_l3_l2": "rgba(40, 120, 40, 0.20)",
            "application_capability_l2": "rgba(255, 127, 14, 0.24)",
        }
    ).fillna("rgba(120, 120, 120, 0.18)")

    height = _dynamic_height(max(len(nodes), len(links)), base=1350, per_item=8, minimum=1350, maximum=12000)
    fig = go.Figure(
        data=[
            go.Sankey(
                node={
                    "label": labels,
                    "color": node_colors.tolist(),
                    "pad": 18,
                    "thickness": 14,
                    "line": {"width": 0.2, "color": "rgba(80, 80, 80, 0.2)"},
                    "customdata": nodes["hover_label"].tolist(),
                    "hovertemplate": "%{customdata}<extra></extra>",
                },
                link={
                    "source": [index[label] for label in links["source_label"]],
                    "target": [index[label] for label in links["target_label"]],
                    "value": links["value"].tolist(),
                    "color": link_colors.tolist(),
                    "customdata": links["hover_label"].tolist(),
                    "hovertemplate": "%{customdata}<extra></extra>",
                },
                arrangement="snap",
            )
        ]
    )
    fig.update_layout(
        title="Entity -> application -> BC L3 -> BC L2",
        autosize=True,
        width=None,
        height=height,
        margin=dict(l=0, r=0, t=60, b=0),
    )
    return fig


def _build_hierarchical_links(model: dict[str, pd.DataFrame], capability_codes: list[str] | None = None) -> pd.DataFrame:
    capabilities = _capability_frame(model)
    bridge = _bridge_frame(model)
    if capabilities.empty or bridge.empty:
        return pd.DataFrame(
            columns=["source_label", "target_label", "value", "kind", "hover_label"]
        )

    closure = model.get("capability_closure", pd.DataFrame()).copy()
    selected_codes = [str(code).strip() for code in (capability_codes or []) if str(code).strip()]
    if selected_codes:
        allowed = _expand_selected_codes(capabilities, closure, selected_codes)
        bridge = bridge[bridge["capability_code"].isin(allowed)]
        capabilities = capabilities[capabilities["code"].isin(allowed)]
    capabilities = capabilities[capabilities["level"].isin([2, 3])]
    if bridge.empty or capabilities.empty:
        return pd.DataFrame(
            columns=["source_label", "target_label", "value", "kind", "hover_label"]
        )

    capability_lookup = capabilities.set_index("code")
    bridge = bridge.merge(
        capability_lookup[["level", "parent_code", "label", "long_name"]],
        left_on="capability_code",
        right_index=True,
        how="left",
        suffixes=("", "_cap"),
    )
    bridge["level"] = pd.to_numeric(bridge["level"], errors="coerce").fillna(0).astype(int)
    bridge["parent_code"] = bridge["parent_code"].fillna("").astype(str).str.strip()
    bridge["application_code"] = bridge["application_code"].fillna("").astype(str).str.strip()
    bridge["entity_code"] = bridge["entity_code"].fillna("").astype(str).str.strip()
    bridge["capability_code"] = bridge["capability_code"].fillna("").astype(str).str.strip()

    applications = _application_directory(model)
    applications = applications[applications["application_code"].isin(bridge["application_code"].unique())].copy()
    if applications.empty:
        return pd.DataFrame(columns=["source_label", "target_label", "value", "kind", "hover_label"])

    app_metrics = (
        bridge.groupby(["application_code", "entity_code"], as_index=False)["capability_code"]
        .size()
        .rename(columns={"size": "outgoing_count"})
    )
    applications = applications.merge(app_metrics, on=["application_code", "entity_code"], how="left")
    applications["outgoing_count"] = applications["outgoing_count"].fillna(0).astype(int)

    rows: list[dict[str, object]] = []

    level3 = bridge[bridge["level"] == 3].copy()
    level2 = bridge[bridge["level"] == 2].copy()
    covered_l2 = {
        (row.application_code, row.parent_code)
        for row in level3.itertuples(index=False)
        if str(row.parent_code or "").strip()
    }
    direct_level2 = level2[
        level2.apply(lambda row: (row["application_code"], row["capability_code"]) not in covered_l2, axis=1)
    ].copy()

    entity_app_rows = pd.concat(
        [
            level3[["application_code", "entity_code"]].copy(),
            direct_level2[["application_code", "entity_code"]].copy(),
        ],
        ignore_index=True,
    )
    if not entity_app_rows.empty:
        entity_app_rows = entity_app_rows.groupby(["application_code", "entity_code"], as_index=False).size().rename(columns={"size": "value"})
        for row in entity_app_rows.itertuples(index=False):
            app_record = applications[
                (applications["application_code"] == row.application_code)
                & (applications["entity_code"] == row.entity_code)
            ]
            if app_record.empty:
                continue
            app_record = app_record.iloc[0]
            entity_label = _format_entity_label(app_record.entity_label)
            app_label = _format_application_label(app_record.entity_label, app_record.application_code)
            rows.append(
                {
                    "source_label": entity_label,
                    "target_label": app_label,
                    "value": int(row.value),
                    "kind": "entity_application",
                    "hover_label": f"{entity_label} → {app_label}<br>Poids: {int(row.value)}",
                }
            )

    if not level3.empty:
        for row in level3.itertuples(index=False):
            app_label = _format_application_label(_entity_label_for_app(applications, row.application_code), row.application_code)
            l3_label = _format_capability_label(row.capability_code)
            rows.append(
                {
                    "source_label": app_label,
                    "target_label": l3_label,
                    "value": 1,
                    "kind": "application_capability_l3",
                    "hover_label": f"{app_label} → {l3_label}<br>{_capability_hover(row.capability_code, row.long_name)}",
                }
            )

        l3_grouped = (
            level3.groupby(["capability_code", "parent_code"], as_index=False)
            .size()
            .rename(columns={"size": "value"})
        )
        for row in l3_grouped.itertuples(index=False):
            l3_label = _format_capability_label(row.capability_code)
            l2_label = _format_capability_label(row.parent_code)
            rows.append(
                {
                    "source_label": l3_label,
                    "target_label": l2_label,
                    "value": int(row.value),
                    "kind": "capability_l3_l2",
                    "hover_label": f"{l3_label} → {l2_label}<br>Poids: {int(row.value)}",
                }
            )

    if not direct_level2.empty:
        for row in direct_level2.itertuples(index=False):
            app_label = _format_application_label(_entity_label_for_app(applications, row.application_code), row.application_code)
            l2_label = _format_capability_label(row.capability_code)
            rows.append(
                {
                    "source_label": app_label,
                    "target_label": l2_label,
                    "value": 1,
                    "kind": "application_capability_l2",
                    "hover_label": f"{app_label} → {l2_label}<br>{_capability_hover(row.capability_code, row.long_name)}",
                }
            )

    frame = pd.DataFrame(rows, columns=["source_label", "target_label", "value", "kind", "hover_label"])
    frame = frame[frame["source_label"] != frame["target_label"]]
    return frame.reset_index(drop=True)


def _build_nodes(model: dict[str, pd.DataFrame], links: pd.DataFrame) -> pd.DataFrame:
    if links.empty:
        return pd.DataFrame(columns=["label", "kind", "hover_label"])

    applications = _application_directory(model)
    linked_app_labels = {
        str(label).strip()
        for label in links.loc[links["kind"].isin(["application_capability_l3", "application_capability_l2"]), "source_label"].dropna().tolist()
        if str(label).strip()
    }
    applications["application_label"] = applications.apply(
        lambda row: _format_application_label(row.entity_label, row.application_code),
        axis=1,
    )
    applications = applications[applications["application_label"].isin(linked_app_labels)].copy()
    if applications.empty:
        return pd.DataFrame(columns=["label", "kind", "hover_label"])

    capabilities = _capability_frame(model)
    app_link_counts = (
        links[links["kind"].isin(["application_capability_l3", "application_capability_l2"])]
        .groupby("source_label", as_index=False)["value"]
        .sum()
        .rename(columns={"value": "capability_links"})
    )
    app_level3_counts = (
        links[links["kind"] == "application_capability_l3"]
        .groupby("source_label", as_index=False)["value"]
        .sum()
        .rename(columns={"value": "l3_links"})
    )
    app_level2_counts = (
        links[links["kind"] == "application_capability_l2"]
        .groupby("source_label", as_index=False)["value"]
        .sum()
        .rename(columns={"value": "l2_links"})
    )
    entity_app_counts = applications.groupby("entity_label").size().to_dict()
    labels: list[dict[str, object]] = []
    seen: set[str] = set()

    for row in applications.itertuples(index=False):
        entity_label = _format_entity_label(row.entity_label)
        app_label = row.application_label
        capability_count = int(app_link_counts.loc[app_link_counts["source_label"] == app_label, "capability_links"].sum())
        l3_count = int(app_level3_counts.loc[app_level3_counts["source_label"] == app_label, "l3_links"].sum())
        l2_count = int(app_level2_counts.loc[app_level2_counts["source_label"] == app_label, "l2_links"].sum())
        if entity_label not in seen:
            labels.append(
                {
                    "label": entity_label,
                    "kind": "entity",
                    "hover_label": f"{entity_label}<br>Entité<br>Applications: {int(entity_app_counts.get(entity_label, 0))}",
                }
            )
            seen.add(entity_label)
        if app_label not in seen:
            labels.append(
                {
                    "label": app_label,
                    "kind": "application",
                    "hover_label": _application_hover(
                        row.entity_label,
                        row.application_code,
                        row.display_name,
                        row.application_name,
                        capability_count=capability_count,
                        l3_count=l3_count,
                        l2_count=l2_count,
                    ),
                }
            )
            seen.add(app_label)

    capability_lookup = capabilities.set_index("code") if not capabilities.empty else pd.DataFrame()
    for code in links.loc[links["kind"] == "application_capability_l3", "target_label"].tolist():
        if code not in seen:
            row = capability_lookup.loc[code] if code in capability_lookup.index else None
            labels.append(
                {
                    "label": code,
                    "kind": "capability_l3",
                    "hover_label": _capability_hover(code, row["long_name"] if row is not None else ""),
                }
            )
            seen.add(code)
    for code in links.loc[links["kind"].isin(["capability_l3_l2", "application_capability_l2"]), "target_label"].tolist():
        if code not in seen:
            row = capability_lookup.loc[code] if code in capability_lookup.index else None
            labels.append(
                {
                    "label": code,
                    "kind": "capability_l2",
                    "hover_label": _capability_hover(code, row["long_name"] if row is not None else ""),
                }
            )
            seen.add(code)

    order = {"entity": 0, "application": 1, "capability_l3": 2, "capability_l2": 3}
    frame = pd.DataFrame(labels)
    frame["kind_order"] = frame["kind"].map(order).fillna(99)
    return frame.sort_values(["kind_order", "label"]).drop(columns=["kind_order"]).reset_index(drop=True)


def _expand_selected_codes(capabilities: pd.DataFrame, closure: pd.DataFrame, selected_codes: list[str]) -> set[str]:
    active = set(selected_codes)
    if closure.empty:
        return active
    descendants = closure[closure["ancestor_code"].isin(selected_codes)]["descendant_code"].astype(str).tolist()
    active.update(descendants)
    parents = capabilities.loc[
        capabilities["code"].isin(active) & capabilities["parent_code"].astype(str).str.strip().ne(""),
        "parent_code",
    ].astype(str).tolist()
    active.update(parents)
    return {code for code in active if code}


def _application_directory(model: dict[str, pd.DataFrame]) -> pd.DataFrame:
    applications = model.get("dim_application", pd.DataFrame()).copy()
    entities = model.get("dim_entity", pd.DataFrame()).copy()
    if applications.empty:
        return pd.DataFrame(columns=["application_code", "entity_code", "entity_label", "application_name", "display_name"])
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
    frame = applications.merge(entities[["entity_code", "entity_label"]].drop_duplicates(), on="entity_code", how="left")
    frame["entity_label"] = frame["entity_label"].fillna("").astype(str).str.strip()
    frame.loc[frame["entity_label"] == "", "entity_label"] = frame.loc[frame["entity_label"] == "", "entity_code"]
    frame["application_name"] = frame["application_name"].fillna("").astype(str).str.strip()
    frame["display_name"] = frame["display_name"].fillna("").astype(str).str.strip()
    return frame[["application_code", "entity_code", "entity_label", "application_name", "display_name"]].drop_duplicates()


def _capability_frame(model: dict[str, pd.DataFrame]) -> pd.DataFrame:
    frame = model.get("dim_business_capability", pd.DataFrame()).copy()
    if frame.empty:
        return pd.DataFrame(columns=["code", "level", "label", "long_name", "parent_code"])
    for column in ["code", "label", "long_name", "parent_code", "level"]:
        if column not in frame.columns:
            frame[column] = ""
    frame["code"] = frame["code"].fillna("").astype(str).str.strip()
    frame["label"] = frame["label"].fillna("").astype(str).str.strip()
    frame["long_name"] = frame["long_name"].fillna("").astype(str).str.strip()
    frame["parent_code"] = frame["parent_code"].fillna("").astype(str).str.strip()
    frame["level"] = pd.to_numeric(frame["level"], errors="coerce").fillna(0).astype(int)
    return frame[frame["code"] != ""].reset_index(drop=True)


def _bridge_frame(model: dict[str, pd.DataFrame]) -> pd.DataFrame:
    bridge = model.get("bridge_application_capability", pd.DataFrame()).copy()
    if bridge.empty:
        return pd.DataFrame(columns=["application_code", "entity_code", "capability_code"])
    for column in ["application_code", "entity_code", "capability_code"]:
        if column not in bridge.columns:
            bridge[column] = ""
        bridge[column] = bridge[column].fillna("").astype(str).str.strip()
    return bridge[(bridge["application_code"] != "") & (bridge["capability_code"] != "")].reset_index(drop=True)


def _format_entity_label(entity_label: object) -> str:
    return str(entity_label or "").strip()


def _format_application_label(entity_label: object, application_code: object) -> str:
    entity_text = str(entity_label or "").strip()
    app_text = str(application_code or "").strip()
    if entity_text and app_text:
        return f"{entity_text}#{app_text}"
    return app_text or entity_text or ""


def _application_hover(
    entity_label: object,
    application_code: object,
    display_name: object,
    application_name: object,
    capability_count: int = 0,
    l3_count: int = 0,
    l2_count: int = 0,
) -> str:
    prefix = _format_application_label(entity_label, application_code)
    display_text = str(display_name or "").strip()
    name_text = str(application_name or "").strip()
    details = [prefix]
    if display_text:
        details.append(display_text)
    if name_text and name_text != display_text:
        details.append(name_text)
    details.append(f"BC links: {capability_count}")
    details.append(f"BC L3: {l3_count}")
    details.append(f"BC L2 direct: {l2_count}")
    return " - ".join(details)


def _entity_label_for_app(applications: pd.DataFrame, application_code: object) -> str:
    code = str(application_code or "").strip()
    if applications.empty or code == "":
        return ""
    match = applications.loc[applications["application_code"] == code, "entity_label"]
    if match.empty:
        return ""
    return str(match.iloc[0])


def _format_capability_label(code: object) -> str:
    return str(code or "").strip()


def _capability_hover(code: object, long_name: object) -> str:
    code_text = str(code or "").strip()
    long_name_text = str(long_name or "").strip()
    if code_text and long_name_text:
        return f"{code_text}#{long_name_text}"
    return code_text or long_name_text or ""


def _dynamic_height(count: int, base: int, per_item: int, minimum: int, maximum: int) -> int:
    return max(minimum, min(maximum, base + count * per_item))
