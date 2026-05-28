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
    excel_browser = mo.ui.file_browser(
        initial_path="..",
        filetypes=[".xlsx"],
        selection_mode="file",
        multiple=False,
        restrict_navigation=False,
        label="Fichier Excel local",
    )
    excel_upload = mo.ui.file(filetypes=[".xlsx"], multiple=False, kind="button", label="Uploader un Excel")
    source_tabs = mo.ui.tabs(
        {
            "Fichier local": mo.vstack([excel_browser]),
            "Upload": mo.vstack([excel_upload]),
        },
        value="Fichier local",
        lazy=True,
        label="Source du fichier",
    )
    cache_dir = mo.ui.text(value="data", label="Dossier cache")
    purge_cache = mo.ui.checkbox(value=True, label="Purger le cache avant écriture")
    auto_refresh = mo.ui.checkbox(value=True, label="Écrire automatiquement le cache au chargement")
    mo.vstack([source_tabs, cache_dir, purge_cache, auto_refresh])
    return auto_refresh, cache_dir, excel_browser, excel_upload, purge_cache, source_tabs


@app.cell
def _(mo):
    status, set_status = mo.state("Cache non généré.")
    return set_status, status


@app.cell
def _(NOTEBOOK_DIR, Path, excel_browser, excel_upload, load_excel_model, sample_model, source_tabs):
    selected_path = None
    if source_tabs.value == "Upload" and excel_upload.value:
        upload_dir = NOTEBOOK_DIR / ".uploads"
        upload_dir.mkdir(parents=True, exist_ok=True)
        uploaded_name = Path(excel_upload.name()).name if excel_upload.name() else "uploaded.xlsx"
        selected_path = upload_dir / uploaded_name
        selected_path.write_bytes(excel_upload.contents())
    elif source_tabs.value == "Fichier local" and excel_browser.value:
        selected_path = Path(excel_browser.path()).expanduser()

    if selected_path and selected_path.exists():
        model = load_excel_model(selected_path)
        data_source = str(selected_path)
    else:
        model = sample_model()
        data_source = f"sample (missing file: {selected_path or 'no file selected'})"
    return data_source, model


@app.cell
def _(NOTEBOOK_DIR, Path, auto_refresh, cache_dir, connect, data_source, mo, model, purge_cache, reset_storage, set_status, write_model):
    def _write_cache() -> None:
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

    if auto_refresh.value:
        _write_cache()

    def _refresh_cache(_event: object) -> None:
        _write_cache()

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
