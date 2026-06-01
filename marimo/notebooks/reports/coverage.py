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

    from src.coverage import candidate_details
    from src.duckdb_repository import connect, empty_model, load_model, storage_exists
    from src.report_helpers import coverage_candidates_display, covering_applications_detail

    return (
        PROJECT_DIR,
        candidate_details,
        connect,
        coverage_candidates_display,
        covering_applications_detail,
        empty_model,
        load_model,
        mo,
        storage_exists,
    )


@app.cell
def _(mo):
    _intro = mo.md(
        "\n".join(
            [
                "# Couverture applicative",
                "",
                "Sélectionne une ligne avec la case à cocher à gauche pour afficher le détail.",
            ]
        )
    )
    _intro


@app.cell
def _(PROJECT_DIR, connect, empty_model, load_model, storage_exists):
    cache_path = (PROJECT_DIR / "data").resolve()
    if storage_exists(cache_path):
        con = connect(cache_path)
        try:
            model = load_model(con)
        finally:
            con.close()
    else:
        model = empty_model()
    return cache_path, model


@app.cell
def _(cache_path, mo):
    _source = mo.md(f"## Source\n\n- **Données**: `{cache_path}`")
    _source


@app.cell
def _(mo):
    threshold = mo.ui.slider(start=0.1, stop=1.0, step=0.05, value=0.8, label="Seuil de couverture")
    scope_mode = mo.ui.dropdown(
        options=["all", "withinEntity", "crossEntity"],
        value="all",
        label="Périmètre",
    )
    controls = mo.hstack([threshold, scope_mode])
    controls


@app.cell
def _(coverage_candidates_display, model, scope_mode, threshold):
    candidates = coverage_candidates_display(
        model,
        threshold=threshold.value,
        entity=None,
        scope_mode=scope_mode.value,
    )
    candidates


@app.cell
def _(candidates, mo):
    _output = None
    if candidates.empty:
        _output = mo.vstack(
            [
                mo.md("## Candidats"),
                mo.md("Aucun candidat de couverture ne correspond aux filtres courants."),
            ]
        )
    else:
        candidate_table = mo.ui.table(
            candidates[
                [
                    "covered_application_detail",
                    "application_code_covered",
                    "covering_application_detail",
                    "application_code_covering",
                    "coverage",
                    "type",
                    "overlap_count",
                    "covered_count",
                    "covering_count",
                ]
            ],
            selection="single",
            pagination=True,
            page_size=25,
            show_data_types=False,
            show_download=False,
            show_column_summaries=False,
            max_height=520,
            format_mapping={"coverage": lambda value: f"{float(value):.0%}"},
            wrapped_columns=["covered_application_detail", "covering_application_detail"],
            label="Candidats de couverture",
        )
        _output = candidate_table
    _output


@app.cell
def _(candidate_table, candidate_details, candidates, covering_applications_detail, model, mo):
    _output = None
    selected = candidate_table.value if candidates.size else None
    debug_value = type(selected).__name__ if selected is not None else "None"
    debug_preview = repr(selected)[:500] if selected is not None else "None"

    def _first_scalar(value):
        if isinstance(value, dict):
            if not value:
                return ""
            return _first_scalar(next(iter(value.values())))
        if isinstance(value, (list, tuple)):
            if not value:
                return ""
            return _first_scalar(value[0])
        return value

    def _normalize_row(obj):
        if hasattr(obj, "iloc") and len(obj):
            obj = obj.iloc[0]
        if hasattr(obj, "to_dict"):
            obj = obj.to_dict()
        if isinstance(obj, dict):
            return {key: _first_scalar(value) for key, value in obj.items()}
        return {}

    if selected is None:
        if candidates.empty:
            _output = mo.vstack(
                [
                    mo.md("## Détail"),
                    mo.md("Aucun candidat de couverture."),
                ]
            )
        else:
            _output = mo.vstack(
                [
                    mo.md("## Détail"),
                    mo.md("Coche une ligne dans le tableau pour afficher le détail."),
                    mo.md(f"- **Sélection brute**: `{debug_value}`"),
                ]
            )
    else:
        row = _normalize_row(selected) or _normalize_row(candidates.iloc[0])

        covered_code = str(row.get("application_code_covered", ""))
        covering_code = str(row.get("application_code_covering", ""))
        pair_details = candidate_details(model, covered_code, covering_code)
        coverers = covering_applications_detail(model, covered_code)

        coverage_value = _first_scalar(row.get("coverage", 0.0))
        try:
            coverage_percent = f"{float(coverage_value):.0%}"
        except Exception:  # pragma: no cover - debug fallback
            coverage_percent = f"{coverage_value}"

        _output = mo.vstack(
            [
                mo.md("## Détail de couverture"),
                mo.md(
                    "\n".join(
                        [
                            f"- **Sélection brute**: `{debug_value}`",
                            f"- **Aperçu sélection**: `{debug_preview}`",
                            f"- **Application couverte**: `{row.get('covered_application_detail', '')}`",
                            f"- **Application couvrante**: `{row.get('covering_application_detail', '')}`",
                            f"- **Couverture**: `{coverage_percent}`",
                            f"- **Type**: `{row.get('type', '')}`",
                        ]
                    )
                ),
                mo.md("### Applications couvrantes"),
                coverers if not coverers.empty else mo.md("Aucune application couvrante trouvée."),
                mo.md("### Capacités communes"),
                pair_details["shared"] if not pair_details["shared"].empty else mo.md("Aucune capacité commune."),
                mo.md("### Capacités manquantes"),
                pair_details["missing"] if not pair_details["missing"].empty else mo.md("Aucune capacité manquante."),
                mo.md("### Capacités en trop"),
                pair_details["extra"] if not pair_details["extra"].empty else mo.md("Aucune capacité en trop."),
            ]
        )
    _output


if __name__ == "__main__":
    app.run()
