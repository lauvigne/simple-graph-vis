# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "marimo",
#     "duckdb>=1.1",
#     "pandas>=2.2",
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
    import pandas as pd

    from src.duckdb_repository import connect, load_model, read_table, storage_exists

    return NOTEBOOK_DIR, PROJECT_DIR, Path, connect, load_model, mo, pd, read_table, storage_exists


@app.cell
def _(mo):
    intro = "\n".join(
        [
            "# Debug DuckDB",
            "",
            "Ce notebook permet d'inspecter les tables présentes dans le cache DuckDB.",
            "Il sert à vérifier ce qui a réellement été écrit après l'ingestion.",
        ]
    )
    mo.md(intro)
    return


@app.cell
def _(mo):
    cache_browser = mo.ui.file_browser(
        initial_path=".",
        selection_mode="directory",
        multiple=False,
        restrict_navigation=False,
        label="Répertoire DuckDB",
    )
    preview_limit = mo.ui.slider(10, 500, value=100, step=10, label="Nombre de lignes à afficher")
    mo.vstack([cache_browser, preview_limit])
    return cache_browser, preview_limit


@app.cell
def _(mo):
    refresh_count, set_refresh_count = mo.state(0)
    return refresh_count, set_refresh_count


@app.cell
def _(
    NOTEBOOK_DIR,
    Path,
    cache_browser,
    connect,
    load_model,
    mo,
    refresh_count,
    storage_exists,
):
    cache_path = NOTEBOOK_DIR / "data"
    if cache_browser.value:
        cache_path = Path(cache_browser.path()).expanduser()
        if not cache_path.is_absolute():
            cache_path = (NOTEBOOK_DIR / cache_path).resolve()

    db_path = cache_path / "local.duckdb"
    status = "Cache introuvable"
    model = {}
    tables = ()
    cache_ready = storage_exists(cache_path)
    if cache_ready:
        _conn = connect(cache_path)
        try:
            model = load_model(_conn)
            tables = tuple(model.keys())
            status = f"Cache chargé depuis {cache_path}"
        finally:
            _conn.close()

    mo.md(
        "\n".join(
            [
                "## État du cache",
                f"- **Chemin**: `{cache_path}`",
                f"- **local.duckdb**: {'présent' if db_path.exists() else 'absent'}",
                f"- **storage_exists**: `{cache_ready}`",
                f"- **Statut**: {status}",
                f"- **Tables**: {len(tables)}",
            ]
        )
    )
    return cache_path, model, tables


@app.cell
def _(mo, refresh_count, set_refresh_count):
    def _refresh_cache(_event: object) -> None:
        set_refresh_count(refresh_count + 1)

    refresh_button = mo.ui.button(
        label="Rafraîchir les données",
        kind="success",
        tooltip="Relit le fichier local.duckdb et recalcule les aperçus",
        on_click=_refresh_cache,
    )
    refresh_button
    return


@app.cell
def _(mo, tables):
    options = list(tables)
    if not options:
        options = ["(aucune table)"]
    table_selector = mo.ui.dropdown(options=options, value=options[0], label="Table à afficher")
    table_selector
    return (table_selector,)


@app.cell
def _(mo, model, pd, table_selector):
    if table_selector.value == "(aucune table)":
        preview = mo.md("### Tables\nAucune table disponible dans ce cache.")
    else:
        frame = model[table_selector.value]
        schema_frame = pd.DataFrame(
            [
                {
                    "colonne": column,
                    "dtype": str(dtype),
                    "non_nulls": int(frame[column].notna().sum()),
                }
                for column, dtype in frame.dtypes.items()
            ]
        )
        summary = mo.md(
            "\n".join(
                [
                    f"### `{table_selector.value}`",
                    f"- **Lignes**: {len(frame)}",
                    f"- **Colonnes**: {len(frame.columns)}",
                ]
            )
        )
        preview = mo.vstack([summary, mo.md("#### Schéma"), schema_frame, mo.md("#### Aperçu"), frame.head(100)])

    preview
    return


@app.cell
def _(cache_path, connect, mo, preview_limit, read_table, table_selector):
    if table_selector.value == "(aucune table)":
        details = mo.md("Aucune requête à exécuter.")
    else:
        _conn = connect(cache_path)
        try:
            sql_preview = read_table(_conn, table_selector.value).head(preview_limit.value)
        finally:
            _conn.close()
        details = mo.vstack(
            [
                mo.md("#### Relecture DuckDB"),
                sql_preview,
            ]
        )
    details
    return


if __name__ == "__main__":
    app.run()
