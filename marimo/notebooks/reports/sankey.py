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

    from src.duckdb_repository import connect, empty_model, load_model, storage_exists
    from src.report_helpers import (
        build_capability_catalog,
        build_leaf_options,
        build_level1_options,
        build_level2_options,
        build_sankey,
        describe_selected_leaves,
    )

    return (
        NOTEBOOK_DIR,
        PROJECT_DIR,
        build_capability_catalog,
        build_leaf_options,
        build_level1_options,
        build_level2_options,
        build_sankey,
        describe_selected_leaves,
        connect,
        empty_model,
        load_model,
        mo,
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
            "# Sankey des applications et capacités",
            "",
            "Ce notebook est dédié au Sankey uniquement.",
            "Il charge le cache DuckDB local et attend une sélection de capacités avant de rendre le graphe.",
        ]
    )
    mo.md(intro)
    return


@app.cell
def _(mo):
    cache_dir = mo.ui.text(value="data", label="Dossier cache DuckDB")
    search_text = mo.ui.text(value="", label="Recherche code ou libellé")
    mo.vstack([cache_dir, search_text])
    return cache_dir, search_text


@app.cell
def _(NOTEBOOK_DIR, Path, cache_dir, connect, empty_model, is_script_mode, load_model, storage_exists):
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
    notice = (
        mo.md(
            "\n".join(
                [
                    "## Cache absent",
                    "",
                    f"Aucune base DuckDB n'a été trouvée dans `{data_source.removeprefix('cache missing: ').strip()}`.",
                    "Lance `ingest.py` pour alimenter `data/local.duckdb`.",
                ]
            )
        )
        if data_source.startswith("cache missing")
        else mo.md("")
    )
    notice
    return


@app.cell
def _(build_capability_catalog, model, mo, search_text):
    catalog = build_capability_catalog(model)
    l1_options = build_level1_options(model, search=search_text.value)
    level1 = mo.ui.dropdown(options=l1_options, value="Tous les niveaux 1", label="Business Capability L1")
    level1
    return catalog, level1


@app.cell
def _(build_level2_options, level1, model, mo, search_text):
    level2_options = build_level2_options(model, search=search_text.value, l1_code=level1.value)
    level2 = mo.ui.dropdown(options=level2_options, value="Tous les niveaux 2", label="Business Capability L2")
    level2
    return level2


@app.cell
def _(build_leaf_options, level1, level2, model, mo, search_text):
    leaf_options = build_leaf_options(model, search=search_text.value, l1_code=level1.value, l2_code=level2.value)
    selected_capabilities = mo.ui.multiselect(
        options=leaf_options,
        value=[],
        label="Capacités à afficher dans le Sankey",
    )
    selected_capabilities
    return selected_capabilities


@app.cell
def _(catalog, describe_selected_leaves, mo, selected_capabilities):
    selected_labels = describe_selected_leaves(
        {"dim_business_capability": catalog},
        selected_capabilities.value,
    )
    if selected_labels:
        summary = mo.md(
            "\n".join(
                [
                    "## Sélection",
                    "",
                    f"{len(selected_labels)} capacité(s) sélectionnée(s).",
                    "",
                    "- " + "\n- ".join(selected_labels[:10]),
                ]
            )
        )
    else:
        summary = mo.md("## Sélection\n\nAucune capacité sélectionnée.")
    summary
    return


@app.cell
def _(build_sankey, mo, model, selected_capabilities):
    selected_codes = selected_capabilities.value
    if not selected_codes:
        sankey_view = mo.md(
            "\n".join(
                [
                    "## Sankey",
                    "",
                    "Sélectionne au moins une capacité pour générer le Sankey.",
                    "Le graphe n'est pas rendu tant qu'aucune capacité n'est choisie, afin d'éviter le chargement complet du réseau.",
                ]
            )
        )
    else:
        sankey_view = build_sankey(model, capability_codes=selected_codes)
    sankey_view
    return


if __name__ == "__main__":
    app.run()
