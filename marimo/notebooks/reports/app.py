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

    from src.report_helpers import build_capability_sunburst, capabilities_table
    from src.duckdb_repository import connect, empty_model, load_model, storage_exists

    return (
        NOTEBOOK_DIR,
        PROJECT_DIR,
        Path,
        build_capability_sunburst,
        capabilities_table,
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
            "# Marimo coverage dataviz",
            "",
            "Ce notebook lit uniquement les tables DuckDB présentes dans `data/`.",
            "Il affiche uniquement le sunburst des business capabilities.",
        ]
    )
    mo.md(intro)
    return


@app.cell
def _(
    PROJECT_DIR,
    Path,
    connect,
    empty_model,
    is_script_mode,
    load_model,
    storage_exists,
):
    cache_path = (PROJECT_DIR / "data").resolve()
    if is_script_mode:
        model = empty_model()
    elif storage_exists(cache_path):
        con = connect(cache_path)
        try:
            model = load_model(con)
        finally:
            con.close()
    else:
        model = empty_model()
    data_source = str(cache_path)
    return data_source, model


@app.cell
def _(data_source, mo):
    cache_notice = (
        mo.md(
            "\n".join(
                [
                    "## Source",
                    "",
                    f"- **Données**: `{data_source}`",
                    "",
                    "Le sunburst utilise la hiérarchie complète L1 > L2 > L3.",
                ]
            )
        )
        if data_source
        else mo.md("")
    )
    cache_notice
    return


@app.cell
def _(mo, model):
    fact_tables = {name: frame for name, frame in model.items() if name.startswith("fact_")}
    counts = {
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
def _(capabilities_table, mo, model):
    capability_rows = capabilities_table(model)
    capability_rows
    return


@app.cell
def _(build_capability_sunburst, mo, model):
    capability_sunburst = build_capability_sunburst(model)
    capability_sunburst
    return


if __name__ == "__main__":
    app.run()
