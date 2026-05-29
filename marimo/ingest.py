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

__generated_with = "0.23.8"
app = marimo.App(width="wide")


@app.cell
def _():
    from pathlib import Path

    import marimo as mo

    from src.config import DEFAULT_CONFIG
    from src.config_io import load_import_config
    from src.ducklake_repository import connect, reset_storage, write_model
    from src.load_excel import load_excel_model, load_workbook
    from src.sample_data import sample_model

    return (
        DEFAULT_CONFIG,
        Path,
        connect,
        load_excel_model,
        load_import_config,
        load_workbook,
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
            "Les notebooks de reporting lisent ensuite uniquement DuckDB.",
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
    config_browser = mo.ui.file_browser(
        initial_path=".",
        filetypes=[".json"],
        selection_mode="file",
        multiple=False,
        restrict_navigation=False,
        label="Config JSON (optionnelle)",
    )
    cache_dir = mo.ui.text(value="data", label="Dossier cache")
    purge_cache = mo.ui.checkbox(value=True, label="Purger le cache avant écriture")
    auto_refresh = mo.ui.checkbox(value=True, label="Écrire automatiquement le cache au chargement")
    mo.vstack([source_tabs, config_browser, cache_dir, purge_cache, auto_refresh])
    return (
        auto_refresh,
        cache_dir,
        config_browser,
        excel_browser,
        excel_upload,
        purge_cache,
        source_tabs,
    )


@app.cell
def _(mo):
    status, set_status = mo.state("Cache non généré.")
    return set_status, status


@app.cell
def _(
    DEFAULT_CONFIG,
    NOTEBOOK_DIR,
    Path,
    config_browser,
    excel_browser,
    excel_upload,
    load_excel_model,
    load_import_config,
    load_workbook,
    sample_model,
    source_tabs,
):
    selected_path = None
    if source_tabs.value == "Upload" and excel_upload.value:
        upload_dir = NOTEBOOK_DIR / ".uploads"
        upload_dir.mkdir(parents=True, exist_ok=True)
        uploaded_name = Path(excel_upload.name()).name if excel_upload.name() else "uploaded.xlsx"
        selected_path = upload_dir / uploaded_name
        selected_path.write_bytes(excel_upload.contents())
    elif source_tabs.value == "Fichier local" and excel_browser.value:
        selected_path = Path(excel_browser.path()).expanduser()

    config = DEFAULT_CONFIG
    config_source = "default"
    if config_browser.value:
        config_path = Path(config_browser.path()).expanduser()
        config = load_import_config(config_path)
        config_source = str(config_path)

    if selected_path and selected_path.exists():
        raw_workbook = load_workbook(selected_path, config)
        model = load_excel_model(selected_path, config)
        data_source = str(selected_path)
    else:
        raw_workbook = {}
        model = sample_model()
        data_source = f"sample (missing file: {selected_path or 'no file selected'})"
    return config_source, data_source, model, raw_workbook


@app.cell
def _(
    NOTEBOOK_DIR,
    Path,
    auto_refresh,
    cache_dir,
    config_source,
    connect,
    data_source,
    mo,
    model,
    purge_cache,
    reset_storage,
    set_status,
    write_model,
):
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
        set_status(f"Cache écrit dans {cache_path.resolve()} depuis {data_source} (config: {config_source})")

    if auto_refresh.value:
        _write_cache()

    def _refresh_cache(_event: object) -> None:
        _write_cache()

    refresh_button = mo.ui.button(
        label="Refresh cache",
        kind="success",
        tooltip="Charge l'Excel courant et réécrit DuckDB",
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


@app.cell
def _(mo, raw_workbook):
    if not raw_workbook:
        preview = mo.md("## Données brutes\nAucune feuille brute chargée.")
    else:
        tabs = {}
        for sheet_key, frame in raw_workbook.items():
            tabs[sheet_key] = mo.vstack(
                [
                    mo.md(
                        "\n".join(
                            [
                                f"**Feuille**: `{sheet_key}`",
                                f"**Dimensions**: {frame.shape[0]} lignes × {frame.shape[1]} colonnes",
                            ]
                        )
                    ),
                    frame.head(50),
                ]
            )

        preview = mo.vstack([mo.md("## Données brutes lues depuis l'Excel"), mo.ui.tabs(tabs, lazy=True)])
    preview
    return


if __name__ == "__main__":
    app.run()
