# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "marimo",
#     "duckdb>=1.1",
#     "pandas>=2.2",
#     "openpyxl>=3.1",
# ]
# ///

import marimo

__generated_with = "0.17.6"
app = marimo.App(width="wide")


@app.cell
def _():
    from pathlib import Path

    import marimo as mo

    from src.ducklake_repository import connect, reset_storage, write_model
    from src.load_excel import load_excel_model
    from src.sample_data import sample_model
    return (
        Path,
        connect,
        load_excel_model,
        mo,
        reset_storage,
        sample_model,
        write_model,
    )


@app.cell
def _(Path):
    NOTEBOOK_DIR = Path(__file__).resolve().parent
    return (NOTEBOOK_DIR,)


@app.cell
def _(mo):
    intro = "\n".join(
        [
            "# Marimo ingestion",
            "",
            "Ce notebook charge l'Excel, construit le modèle analytique puis réécrit `data/`.",
            "Les notebooks de reporting lisent ensuite uniquement DuckDB/DuckLake.",
        ]
    )
    mo.md(intro)
    return


@app.cell
def _(mo):
    excel_path = mo.ui.text(value="../bian_business_capabilities.xlsx", label="Fichier Excel")
    cache_dir = mo.ui.text(value="data", label="Dossier cache")
    purge_cache = mo.ui.checkbox(value=True, label="Purger le cache avant écriture")
    mo.vstack([excel_path, cache_dir, purge_cache])
    return cache_dir, excel_path, purge_cache


@app.cell
def _(mo):
    status, set_status = mo.state("Cache non généré.")
    return set_status, status


@app.cell
def _(Path, excel_path, load_excel_model, sample_model):
    selected_path = Path(excel_path.value).expanduser()
    if selected_path.exists():
        model = load_excel_model(selected_path)
        data_source = str(selected_path)
    else:
        model = sample_model()
        data_source = f"sample (missing file: {selected_path})"
    return data_source, model


@app.cell
def _(NOTEBOOK_DIR, Path, cache_dir, connect, data_source, mo, model, purge_cache, reset_storage, set_status, write_model):
    def _refresh_cache(_event: object) -> None:
        cache_path = Path(cache_dir.value).expanduser()
        if not cache_path.is_absolute():
            cache_path = (NOTEBOOK_DIR / cache_path).resolve()
        if purge_cache.value:
            reset_storage(cache_path)
        con = connect(cache_path)
        try:
            write_model(con, model)
        finally:
            con.close()
        set_status(f"Cache écrit dans {cache_path.resolve()} depuis {data_source}")

    refresh_button = mo.ui.button(
        label="Refresh cache",
        kind="success",
        tooltip="Charge l'Excel courant et réécrit DuckDB/DuckLake",
        on_click=_refresh_cache,
    )
    refresh_button
    return


@app.cell
def _(data_source, mo, model, status):
    counts = {
        "Source": data_source,
        "Applications": len(model["dim_application"]),
        "Entités": len(model["dim_entity"]),
        "Capacités": len(model["dim_business_capability"]),
        "Mappings": len(model["bridge_application_capability"]),
        "Warnings": len(model["import_warnings"]),
    }
    mo.md(
        "\n".join(
            [
                "## Aperçu",
                *[f"- **{key}**: {value}" for key, value in counts.items()],
                "",
                f"**Statut cache**: {status}",
            ]
        )
    )
    return


if __name__ == "__main__":
    app.run()
