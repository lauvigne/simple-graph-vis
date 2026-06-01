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

    from reports.report_capabilities import capabilities_table, duplicate_capabilities
    from reports.report_mapping import query_candidates
    from reports.report_visuals import build_capability_sunburst, build_mapping_sankey
    from src.coverage import candidate_details
    from src.duckdb_repository import connect, empty_model, load_model, storage_exists

    return (
        Path,
        build_capability_sunburst,
        build_mapping_sankey,
        capabilities_table,
        connect,
        duplicate_capabilities,
        empty_model,
        load_model,
        mo,
        query_candidates,
        storage_exists,
    )


@app.cell
def _(Path):
    NOTEBOOK_DIR = Path(__file__).resolve().parent
    return (NOTEBOOK_DIR,)


@app.cell
def _(mo):
    is_script_mode = mo.app_meta().mode == "script"
    return (is_script_mode,)


@app.cell
def _(mo):
    intro = "\n".join(
        [
            "# Marimo coverage dataviz",
            "",
            "Ce notebook lit uniquement les tables DuckDB présentes dans `data/`.",
            "Le chargement Excel est déplacé dans `ingest.py`.",
        ]
    )
    mo.md(intro)
    return


@app.cell
def _(mo):
    cache_dir = mo.ui.text(value="data", label="Dossier data")
    threshold = mo.ui.slider(start=0.1, stop=1.0, step=0.05, value=0.8, label="Seuil de couverture")
    scope_mode = mo.ui.dropdown(options=["all", "withinEntity", "crossEntity"], value="all", label="Périmètre")
    show_plots = mo.ui.switch(value=False, label="Afficher les graphiques avancés")
    mo.vstack([cache_dir, threshold, scope_mode, show_plots])
    return cache_dir, scope_mode, show_plots, threshold


@app.cell
def _(
    NOTEBOOK_DIR,
    Path,
    cache_dir,
    connect,
    empty_model,
    is_script_mode,
    load_model,
    storage_exists,
):
    cache_path = Path(cache_dir.value).expanduser()
    if not cache_path.is_absolute():
        cache_path = (NOTEBOOK_DIR / cache_path).resolve()
    if is_script_mode:
        model = empty_model()
        data_source = "sample"
    elif storage_exists(cache_path):
        con = connect(cache_path)
        try:
            model = load_model(con)
        finally:
            con.close()
        data_source = str(cache_path)
    else:
        model = empty_model()
        data_source = f"cache missing: {cache_path}"
    return data_source, model


@app.cell
def _(data_source, mo):
    cache_notice = (
        mo.md(
            "\n".join(
                [
                    "## Cache absent",
                    "",
                    f"Aucune base DuckDB n'a été trouvée dans `{data_source.removeprefix('cache missing: ').strip()}`.",
                    "Lance `ingest.py` pour charger l'Excel puis rafraîchir `data/`.",
                ]
            )
        )
        if data_source.startswith("cache missing")
        else mo.md("")
    )
    cache_notice
    return


@app.cell
def _(data_source, mo, model):
    fact_tables = {name: frame for name, frame in model.items() if name.startswith("fact_")}
    counts = {
        "Source": data_source,
        "Applications": len(model["dim_application"]),
        "Entités": len(model["dim_entity"]),
        "Capacités": len(model["dim_business_capability"]),
        "Mappings": len(model["bridge_application_capability"]),
        "Warnings": len(model["import_warnings"]),
    }
    if fact_tables:
        counts["Facts"] = ", ".join(f"{name}={len(frame)}" for name, frame in sorted(fact_tables.items()))
    mo.md(
        "\n".join(
            [
                "## Synthèse",
                *[f"- **{key}**: {value}" for key, value in counts.items()],
            ]
        )
    )
    return


@app.cell
def _(capabilities_table, model):
    capability_rows = capabilities_table(model)
    capability_rows
    return


@app.cell
def _(duplicate_capabilities, model):
    duplicate_rows = duplicate_capabilities(model)
    duplicate_rows
    return


@app.cell
def _(model, query_candidates, scope_mode, threshold):
    candidates = query_candidates(model, threshold=threshold.value, entity=None, scope_mode=scope_mode.value)
    candidates
    return


@app.cell
def _(build_capability_sunburst, build_mapping_sankey, mo, model, show_plots):
    if show_plots.value:
        capability_sunburst = build_capability_sunburst(model)
        mapping_sankey = build_mapping_sankey(model)
        result = mo.ui.tabs(
            {
                "Sunburst": capability_sunburst,
                "Sankey": mapping_sankey,
            },
            lazy=True,
            value="Sunburst",
            label="Graphiques",
        )
    else:
        result = mo.md("Les graphiques avancés sont masqués. Active `Afficher les graphiques avancés` pour les ouvrir dans des onglets séparés.")
    result
    return


if __name__ == "__main__":
    app.run()
