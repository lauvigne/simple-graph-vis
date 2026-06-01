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
    intro = "\n".join(
        [
            "# Treemap des business capabilities",
            "",
            "Ce notebook affiche un treemap des capacités métiers avec deux métriques:",
            "- nombre d'applications",
            "- nombre d'incidents",
            "",
            "Le treemap descend de L1 > L2 > L3 puis affiche les applications en 4e niveau lors du zoom.",
            "",
            "Les applications ne sont affichées qu'à partir des capacités de niveau 3.",
        ]
    )
    mo.md(intro)
    return


@app.cell
def _(mo):
    metric_selector = mo.ui.dropdown(
        options=["applications", "incidents"],
        value="applications",
        label="Métrique",
    )
    mo.vstack([mo.md("**Données**: `data/local.duckdb`"), metric_selector])
    return metric_selector


@app.cell
def _(PROJECT_DIR, connect, empty_model, load_model, metric_selector, storage_exists):
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
def _(data_source, mo):
    mo.md(
        "\n".join(
            [
                "## Source",
                f"- **Données**: `{data_source}`",
                "",
                "Le treemap utilise la hiérarchie complète L1 > L2 > L3 et affiche les applications au 4e niveau lors du zoom. Les valeurs exactes sont affichées en infobulle et dans le tableau sous le graphique.",
            ]
        )
    )
    return


@app.cell
def _(build_treemap_data, build_treemap_figure, metric_selector, model):
    treemap_frame = build_treemap_data(model, metric_selector.value)
    treemap_figure = build_treemap_figure(treemap_frame, metric_selector.value)
    return treemap_figure, treemap_frame


@app.cell
def _(mo, metric_selector, model, treemap_frame):
    incidents_frame = model.get("fact_incidents")
    incidents_total = 0 if incidents_frame is None or incidents_frame.empty else int(incidents_frame["incident_count"].sum())
    if metric_selector.value == "incidents" and incidents_total == 0:
        notice = mo.md(
            "\n".join(
                [
                    "## Incidents",
                    "",
                    "Aucune donnée d'incidents n'est disponible dans le cache. La métrique incidents est donc vide.",
                ]
            )
        )
    else:
        notice = mo.md("")
    notice
    return


@app.cell
def _(mo, treemap_figure):
    treemap_figure
    return


@app.cell
def _(mo, treemap_frame):
    if treemap_frame.empty:
        preview = mo.md("## Agrégats\nAucune capacité à afficher.")
    else:
        columns = ["kind", "code", "label", "long_name", "metric_value", "tree_weight", "level", "parent_code", "application_code", "entity_code"]
        preview = mo.vstack(
            [
                mo.md("## Agrégats"),
                mo.md("`metric_value` = valeur directe, `tree_weight` = valeur cumulée sur la branche. Les lignes de type `application` apparaissent au 4e niveau."),
                treemap_frame[columns].sort_values(["metric_value", "code"], ascending=[False, True]).head(100),
            ]
        )
    preview
    return


if __name__ == "__main__":
    app.run()
