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

    from src.report_helpers import capabilities_table, duplicate_capabilities, query_candidates, build_capability_sunburst, build_mapping_sankey
    from src.coverage import candidate_details
    from src.duckdb_repository import connect, empty_model, load_model, storage_exists

    return (
        NOTEBOOK_DIR,
        PROJECT_DIR,
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
    focus_graphs = mo.ui.switch(value=False, label="Focus graphique")
    mo.vstack([cache_dir, threshold, scope_mode, show_plots, focus_graphs])
    return cache_dir, focus_graphs, scope_mode, show_plots, threshold


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
        cache_path = (PROJECT_DIR / cache_path).resolve()
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
def _(data_source, focus_graphs, mo, model):
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
def _(mo, model):
    capabilities = model["dim_business_capability"].sort_values(["path_l1", "path_l2", "path_l3", "code"])
    capability_filter = mo.ui.multiselect(
        options={f"{row.code} - {row.long_name or row.label}": row.code for row in capabilities.itertuples(index=False) if str(row.code).strip()},
        value=[],
        label="Filtrer le Sankey par capacités",
    )
    capability_filter
    return (capability_filter,)


@app.cell
def _(capabilities_table, focus_graphs, mo, model):
    capability_rows = capabilities_table(model)
    capability_view = capability_rows if not focus_graphs.value else mo.md("")
    capability_view
    return


@app.cell
def _(duplicate_capabilities, focus_graphs, mo, model):
    duplicate_rows = duplicate_capabilities(model)
    duplicate_view = duplicate_rows if not focus_graphs.value else mo.md("")
    duplicate_view
    return


@app.cell
def _(focus_graphs, mo, model, query_candidates, scope_mode, threshold):
    candidates = query_candidates(model, threshold=threshold.value, entity=None, scope_mode=scope_mode.value)
    candidates_view = candidates if not focus_graphs.value else mo.md("")
    candidates_view
    return


@app.cell
def _(build_capability_sunburst, build_mapping_sankey, capability_filter, focus_graphs, mo, model, show_plots):
    if show_plots.value:
        capability_sunburst = build_capability_sunburst(model)
        mapping_sankey = build_mapping_sankey(model, capability_codes=capability_filter.value)
        if focus_graphs.value:
            graphs_view = mo.vstack(
                [
                    mo.md(
                        "\n".join(
                            [
                                "## Focus graphique",
                                "",
                                "Mode lecture large activé: les tableaux sont masqués pour laisser un maximum de place aux diagrammes.",
                            ]
                        )
                    ),
                    mo.ui.tabs(
                        {
                            "Sunburst": capability_sunburst,
                            "Sankey": mapping_sankey,
                        },
                        lazy=True,
                        value="Sunburst",
                        label="Graphiques",
                    ),
                ]
            )
        else:
            graphs_view = mo.ui.tabs(
                {
                    "Sunburst": capability_sunburst,
                    "Sankey": mapping_sankey,
                },
                lazy=True,
                value="Sunburst",
                label="Graphiques",
            )
    else:
        graphs_view = mo.md("Les graphiques avancés sont masqués. Active `Afficher les graphiques avancés` pour les ouvrir dans des onglets séparés.")
    graphs_view
    return


@app.cell
def _(mo, show_plots):
    if show_plots.value:
        legend = mo.md(
            "\n".join(
                [
                    "## Légende des couleurs",
                    "",
                    "- **Bleu**: applications",
                    "- **Vert**: capacités métiers",
                    "",
                    "Les couleurs distinguent les types de nœuds. Le Sankey n’a pas de légende native vraiment lisible, donc on l’explicite ici.",
                ]
            )
        )
    else:
        legend = mo.md("")
    legend
    return


if __name__ == "__main__":
    app.run()
