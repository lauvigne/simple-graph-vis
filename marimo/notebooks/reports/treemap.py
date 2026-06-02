# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "marimo",
#     "duckdb>=1.1",
#     "pandas>=2.2",
#     "plotly>=5.24",
# ]
# ///

import marimo

__generated_with = "0.23.8"
app = marimo.App(width="full")


@app.cell
def _():
    import sys
    from pathlib import Path

    NOTEBOOK_DIR = Path(__file__).resolve().parent
    PROJECT_DIR = NOTEBOOK_DIR.parent.parent
    if str(PROJECT_DIR) not in sys.path:
        sys.path.insert(0, str(PROJECT_DIR))

    import marimo as mo

    from src.report_helpers import build_treemap_data, build_treemap_figure
    from src.duckdb_repository import connect, empty_model, load_model, storage_exists

    return NOTEBOOK_DIR, PROJECT_DIR, Path, build_treemap_data, build_treemap_figure, connect, empty_model, load_model, mo, storage_exists


@app.cell
def _(mo):
    intro = mo.md(
        "\n".join(
            [
                "# Treemap des business capabilities",
                "",
                "Ce notebook affiche un treemap des capacités métiers avec deux métriques:",
                "- nombre d'applications",
                "- nombre d'incidents",
                "",
                "Le treemap descend de L1 > L2 > L3 puis affiche les applications en 4e niveau lors du zoom.",
                "Les capacités L3 affichent `code - nom long` quand c'est lisible, avec un tooltip toujours détaillé.",
            ]
        )
    )
    intro


@app.cell
def _(mo):
    metric_selector = mo.ui.dropdown(
        options=["applications", "incidents"],
        value="applications",
        label="Métrique",
    )
    return (metric_selector,)


@app.cell
def _(PROJECT_DIR, connect, empty_model, load_model, storage_exists):
    cache_path = (PROJECT_DIR / "data").resolve()
    if storage_exists(cache_path):
        conn = connect(cache_path)
        try:
            model = load_model(conn)
        finally:
            conn.close()
        data_source = str(cache_path)
    else:
        model = empty_model()
        data_source = "sample"
    return cache_path, data_source, model


@app.cell
def _(model, mo):
    entity_lookup = {"Toutes les entités": None}
    entity_labels = ["Toutes les entités"]
    entities = model.get("dim_entity")
    if entities is not None and not entities.empty and "entity_code" in entities.columns:
        entity_rows = entities[["entity_code", "label"]].copy()
        entity_rows["entity_code"] = entity_rows["entity_code"].fillna("").astype(str).str.strip()
        entity_rows["label"] = entity_rows["label"].fillna("").astype(str).str.strip()
        entity_rows.loc[entity_rows["label"] == "", "label"] = entity_rows.loc[entity_rows["label"] == "", "entity_code"]
        entity_rows = entity_rows[entity_rows["entity_code"] != ""].sort_values(["label", "entity_code"]).reset_index(drop=True)
    for _, row in entity_rows.iterrows():
        option_label = f"{row['label']} ({row['entity_code']})"
        entity_lookup[option_label] = str(row["entity_code"])
        entity_labels.append(option_label)
    entity_selector = mo.ui.dropdown(options=entity_labels, value="Toutes les entités", label="Entité")
    return entity_lookup, entity_selector


@app.cell
def _(metric_selector, model, mo):
    incident_years_available: list[int] = []
    incidents = model.get("fact_incidents")
    if incidents is not None and not incidents.empty and "year" in incidents.columns:
        incident_years_available = (
            incidents["year"]
            .dropna()
            .astype(int)
            .sort_values()
            .drop_duplicates()
            .tolist()
        )

    incident_years = mo.ui.multiselect(
        options=incident_years_available,
        value=incident_years_available,
        label="Années d'incident",
    )
    incident_type_p1 = mo.ui.checkbox(value=True, label="P1")
    incident_type_p2 = mo.ui.checkbox(value=True, label="P2")
    normalize_incidents = mo.ui.checkbox(
        value=False,
        label="Normaliser par le nombre d'applications",
        disabled=metric_selector.value != "incidents",
    )
    return incident_years, incident_type_p1, incident_type_p2, normalize_incidents


@app.cell
def _(entity_selector, incident_type_p1, incident_type_p2, incident_years, metric_selector, mo, normalize_incidents):
    if metric_selector.value == "incidents":
        controls = mo.vstack(
            [
                mo.hstack([metric_selector, entity_selector, normalize_incidents, incident_years, incident_type_p1, incident_type_p2])
            ]
        )
    else:
        controls = mo.hstack([metric_selector, entity_selector])
    controls


# @app.cell
# def _(data_source, mo):
#     mo.md(
#         "\n".join(
#             [
#                 "## Source",
#                 f"- **Données**: `{data_source}`",
#                 "",
#                 "Le treemap utilise la hiérarchie complète L1 > L2 > L3 et affiche les applications au 4e niveau lors du zoom.",
#             ]
#         )
#     )
#     return


@app.cell
def _(
    build_treemap_data,
    build_treemap_figure,
    entity_lookup,
    entity_selector,
    incident_type_p1,
    incident_type_p2,
    incident_years,
    metric_selector,
    model,
    normalize_incidents,
):
    selected_entity_code = entity_lookup.get(entity_selector.value)
    selected_incident_years = list(incident_years.value) if metric_selector.value == "incidents" else None
    selected_incident_types: list[int] | None = None
    if metric_selector.value == "incidents":
        selected_incident_types = []
        if incident_type_p1.value:
            selected_incident_types.append(1)
        if incident_type_p2.value:
            selected_incident_types.append(2)

    treemap_frame = build_treemap_data(
        model,
        metric_selector.value,
        entity_code=selected_entity_code,
        incident_years=selected_incident_years,
        incident_types=selected_incident_types,
        normalize_incidents=normalize_incidents.value,
    )
    treemap_figure = build_treemap_figure(
        treemap_frame,
        metric_selector.value,
        normalize_incidents=normalize_incidents.value,
    )
    return treemap_figure, treemap_frame


@app.cell
def _(metric_selector, model, mo, normalize_incidents):
    incidents_frame = model.get("fact_incidents")
    incidents_total = 0 if incidents_frame is None or incidents_frame.empty else int(incidents_frame["incident_count"].sum())
    if metric_selector.value == "incidents" and incidents_total == 0:
        notice = mo.md(
            "\n".join(
                [
                    "## Incidents",
                    "Aucune donnée d'incidents n'est disponible dans le cache. La métrique incidents est donc vide.",
                ]
            )
        )
    elif metric_selector.value == "incidents" and normalize_incidents.value:
        notice = mo.md(
            "\n".join(
                [
                    "## Incidents normalisés",
                    "La couleur des capacités L3 reflète le ratio `incidents / applications distinctes`.",
                ]
            )
        )
    else:
        notice = mo.md("")
    notice


@app.cell
def _(metric_selector, mo, normalize_incidents, treemap_figure):
    if metric_selector.value == "incidents" and normalize_incidents.value:
        legend_title = "### Légende ratio L3"
    else:
        legend_title = "### Légende"

    legend = mo.md(
        "\n".join(
            [
                legend_title,
                "",
                "- <span style='display:inline-block;width:12px;height:12px;background:#2ca02c;border:1px solid #999;margin-right:6px;vertical-align:middle;'></span> L3 faible",
                "- <span style='display:inline-block;width:12px;height:12px;background:#4fba74;border:1px solid #999;margin-right:6px;vertical-align:middle;'></span> L3 moyen",
                "- <span style='display:inline-block;width:12px;height:12px;background:#1f77b4;border:1px solid #999;margin-right:6px;vertical-align:middle;'></span> L3 élevé",
                "",
                "Les niveaux L1/L2 restent en couleur neutre pour conserver la lecture de la hiérarchie.",
            ]
        )
    )
    mo.vstack([treemap_figure, legend])
    return

if __name__ == "__main__":
    app.run()
