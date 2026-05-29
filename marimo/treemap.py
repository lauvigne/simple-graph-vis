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
app = marimo.App(width="wide")


@app.cell
def _():
    from pathlib import Path

    import marimo as mo

    from reports.report_treemap import build_treemap_data, build_treemap_figure
    from src.ducklake_repository import connect, load_model, storage_exists
    from src.sample_data import sample_model

    return Path, build_treemap_data, build_treemap_figure, connect, load_model, mo, sample_model, storage_exists


@app.cell
def _(Path):
    NOTEBOOK_DIR = Path(__file__).resolve().parent
    return (NOTEBOOK_DIR,)


@app.cell
def _(mo):
    intro = "\n".join(
        [
            "# Treemap des business capabilities",
            "",
            "Ce notebook affiche un treemap des capacités métiers avec deux métriques:",
            "- nombre d'applications",
            "- nombre d'incidents",
        ]
    )
    mo.md(intro)
    return


@app.cell
def _(mo):
    cache_dir = mo.ui.text(value="data", label="Dossier data")
    metric_selector = mo.ui.dropdown(
        options=["applications", "incidents"],
        value="applications",
        label="Métrique",
    )
    mo.vstack([cache_dir, metric_selector])
    return cache_dir, metric_selector


@app.cell
def _(NOTEBOOK_DIR, Path, cache_dir, connect, load_model, metric_selector, sample_model, storage_exists):
    cache_path = Path(cache_dir.value).expanduser()
    if not cache_path.is_absolute():
        cache_path = (NOTEBOOK_DIR / cache_path).resolve()

    if storage_exists(cache_path):
        conn = connect(cache_path)
        try:
            model = load_model(conn)
        finally:
            conn.close()
        data_source = str(cache_path)
    else:
        model = sample_model()
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
                "Le treemap utilise la hiérarchie complète L1 > L2 > L3. Les valeurs exactes sont affichées en infobulle et dans le tableau sous le graphique.",
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
        columns = ["code", "label", "long_name", "metric_value", "tree_weight", "level", "parent_code"]
        preview = mo.vstack(
            [
                mo.md("## Agrégats"),
                mo.md("`metric_value` = valeur directe, `tree_weight` = valeur cumulée sur la branche."),
                treemap_frame[columns].sort_values(["metric_value", "code"], ascending=[False, True]).head(100),
            ]
        )
    preview
    return


if __name__ == "__main__":
    app.run()
