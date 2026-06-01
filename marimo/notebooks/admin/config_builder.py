# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "marimo",
#     "pandas>=2.2",
#     "openpyxl>=3.1",
# ]
# ///

import marimo

__generated_with = "0.23.8"
app = marimo.App(width="full")


@app.cell
def _():
    import json
    from pathlib import Path

    import marimo as mo

    from src.config import DEFAULT_CONFIG
    from src.config_io import import_config_from_dict, import_config_to_dict, save_import_config

    return (
        NOTEBOOK_DIR,
        PROJECT_DIR,
        DEFAULT_CONFIG,
        Path,
        import_config_from_dict,
        import_config_to_dict,
        json,
        mo,
        save_import_config,
    )


@app.cell
def _(mo):
    mo.md(
        "\n".join(
            [
                "# Marimo config builder",
                "",
                "Édite ici le JSON de paramétrage des sources, puis sauvegarde-le pour `ingest.py`.",
                "Le notebook peut servir de point d'entrée pour ajouter des sources sans toucher au code métier.",
            ]
        )
    )
    return


@app.cell
def _(DEFAULT_CONFIG, import_config_to_dict, json, mo):
    config_text = mo.ui.code_editor(
        value=json.dumps(import_config_to_dict(DEFAULT_CONFIG), indent=2, ensure_ascii=False),
        language="json",
        min_height=500,
        label="Config JSON",
    )
    output_path = mo.ui.text(value="configs/working-config.json", label="Fichier de sortie")
    workbook_browser = mo.ui.file_browser(
        initial_path="..",
        filetypes=[".xlsx"],
        selection_mode="file",
        multiple=False,
        label="Workbook à inspecter",
    )
    mo.vstack([workbook_browser, output_path, config_text])
    return config_text, output_path


@app.cell
def _(config_text, import_config_from_dict, json, mo):
    try:
        parsed = import_config_from_dict(json.loads(config_text.value))
        status = mo.md(
            "\n".join(
                [
                    "## Validation",
                    f"- hierarchy sheets: {len(parsed.hierarchy_sheets)}",
                    f"- mapping sheets: {len(parsed.mapping_sheets)}",
                    f"- fact sheets: {len(parsed.fact_sheets)}",
                ]
            )
        )
    except Exception as exc:
        status = mo.md(f"## Validation\n\n`{exc}`")
    status
    return


@app.cell
def _(
    NOTEBOOK_DIR,
    Path,
    config_text,
    import_config_from_dict,
    json,
    mo,
    output_path,
    save_import_config,
):
    def _save(_event: object) -> None:
        payload = json.loads(config_text.value)
        config = import_config_from_dict(payload, base_dir=NOTEBOOK_DIR)
        target = Path(output_path.value).expanduser()
        if not target.is_absolute():
            target = (NOTEBOOK_DIR / target).resolve()
        save_import_config(config, target)

    save_button = mo.ui.button(
        label="Sauvegarder le JSON",
        kind="success",
        on_click=_save,
    )
    save_button
    return


if __name__ == "__main__":
    app.run()
