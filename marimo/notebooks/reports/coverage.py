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

    from src.coverage import candidate_details
    from src.duckdb_repository import connect, empty_model, load_model, storage_exists
    from src.report_helpers import coverage_candidates_display, covering_applications_detail

    return (
        NOTEBOOK_DIR,
        PROJECT_DIR,
        Path,
        candidate_details,
        connect,
        coverage_candidates_display,
        covering_applications_detail,
        empty_model,
        load_model,
        mo,
        pd,
        storage_exists,
    )


@app.cell
def _(mo):
    mo.md(
        "\n".join(
            [
                "# Couverture applicative",
                "",
                "Le tableau des candidats est cliquable.",
                "Les listes déroulantes de secours servent à retrouver rapidement une application si besoin.",
            ]
        )
    )
    return


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
    mo.md(f"## Source\n\n- **Données**: `{cache_path}`")
    return


@app.cell
def _(mo):
    threshold = mo.ui.slider(start=0.1, stop=1.0, step=0.05, value=0.8, label="Seuil de couverture")
    scope_mode = mo.ui.dropdown(
        options=["all", "withinEntity", "crossEntity"],
        value="all",
        label="Périmètre",
    )
    mo.hstack([threshold, scope_mode])
    return scope_mode, threshold


@app.cell
def _(coverage_candidates_display, model, scope_mode, threshold):
    candidates = coverage_candidates_display(
        model,
        threshold=threshold.value,
        entity=None,
        scope_mode=scope_mode.value,
    )
    return (candidates,)


@app.cell
def _(candidates, mo):
    if candidates.empty:
        candidate_table = mo.md("Aucun candidat de couverture ne correspond aux filtres courants.")
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
            initial_selection=[0],
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
    candidate_table
    return candidate_table


@app.cell
def _(candidates, mo):
    if candidates.empty:
        covered_selector = mo.ui.dropdown(
            options={"Aucune application": ""},
            value="Aucune application",
            label="Application couverte",
            disabled=True,
            searchable=True,
            full_width=True,
        )
    else:
        _covered_options = {
            str(row["covered_application_detail"]): str(row["application_code_covered"])
            for _, row in candidates[["covered_application_detail", "application_code_covered"]].drop_duplicates().iterrows()
        }
        covered_selector = mo.ui.dropdown(
            options=_covered_options,
            value=next(iter(_covered_options.keys())),
            label="Application couverte",
            searchable=True,
            full_width=True,
        )
    mo.vstack(
        [
            mo.md("### Sélecteur de secours - application couverte"),
            covered_selector,
        ]
    )
    return covered_selector


@app.cell
def _(candidate_table, candidates, covered_selector, mo):
    if candidates.empty:
        covering_selector = mo.ui.dropdown(
            options={"Aucune couverture": ""},
            value="Aucune couverture",
            label="Application couvrante",
            disabled=True,
            searchable=True,
            full_width=True,
        )
    else:
        _selected_rows_covering = candidate_table.value
        selected_row_covering = _selected_rows_covering.iloc[0] if hasattr(_selected_rows_covering, "iloc") and len(_selected_rows_covering) else None
        if selected_row_covering is not None:
            _covered_code = str(selected_row_covering["application_code_covered"])
        else:
            _covered_code = covered_selector.value
            _covered_code = candidates.loc[
                candidates["covered_application_detail"] == _covered_code, "application_code_covered"
            ]
            _covered_code = str(_covered_code.iloc[0]) if len(_covered_code) else ""

        _covering_options = {
            str(row["covering_application_detail"]): str(row["application_code_covering"])
            for _, row in candidates[candidates["application_code_covered"] == _covered_code][
                ["covering_application_detail", "application_code_covering"]
            ]
            .drop_duplicates()
            .iterrows()
        }
        if not _covering_options:
            _covering_options = {"Aucune couverture": ""}
        covering_selector = mo.ui.dropdown(
            options=_covering_options,
            value=next(iter(_covering_options.keys())),
            label="Application couvrante",
            searchable=True,
            full_width=True,
        )
    mo.vstack(
        [
            mo.md("### Sélecteur de secours - application couvrante"),
            covering_selector,
        ]
    )
    return covering_selector


@app.cell
def _(candidate_details, candidates, covering_selector, covering_applications_detail, mo, model, covered_selector, candidate_table):
    if candidates.empty:
        detail = mo.md("## Détail\n\nAucun candidat de couverture ne correspond aux filtres courants.")
    else:
        _selected_rows_detail = candidate_table.value
        selected_row_detail = _selected_rows_detail.iloc[0] if hasattr(_selected_rows_detail, "iloc") and len(_selected_rows_detail) else None
        if selected_row_detail is not None:
            _covered_code = str(selected_row_detail["application_code_covered"])
            _covering_code = str(selected_row_detail["application_code_covering"])
            _selected_covering_label = str(selected_row_detail["covering_application_detail"])
        else:
            _covered_code = str(
                candidates.loc[candidates["covered_application_detail"] == covered_selector.value, "application_code_covered"].iloc[0]
            )
            _covering_code = str(
                candidates.loc[
                    (candidates["application_code_covered"] == _covered_code)
                    & (candidates["covering_application_detail"] == covering_selector.value),
                    "application_code_covering",
                ].iloc[0]
            )
            _selected_covering_label = covering_selector.value

        pair_details = candidate_details(model, _covered_code, _covering_code)
        coverers = covering_applications_detail(model, _covered_code)

        detail = mo.vstack(
            [
                mo.md(
                    "\n".join(
                        [
                            "## Détail de couverture",
                            "",
                            f"- **Application couverte**: `{covered_selector.value}`",
                            f"- **Application couvrante**: `{_selected_covering_label}`",
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
    detail
    return


@app.cell
def _(candidates, mo):
    if candidates.empty:
        summary = mo.md(
            "\n".join(
                [
                    "## Synthèse",
                    "",
                    "- **Candidats**: 0",
                    "- Aucun recouvrement trouvé avec les filtres actuels.",
                ]
            )
        )
    else:
        summary = mo.md(
            "\n".join(
                [
                    "## Synthèse",
                    "",
                    f"- **Candidats**: {len(candidates)}",
                    f"- **Applications couvertes distinctes**: {candidates['application_code_covered'].nunique()}",
                    f"- **Applications couvrantes distinctes**: {candidates['application_code_covering'].nunique()}",
                    "- **Sélection**: clique une ligne du tableau pour afficher le détail.",
                ]
            )
        )
    summary
    return


@app.cell
def _(candidate_table, mo):
    mo.vstack(
        [
            mo.md(
                "\n".join(
                    [
                        "## Candidats",
                        "",
                        "Clique une ligne du tableau pour afficher le détail en dessous.",
                    ]
                )
            ),
            candidate_table,
        ]
    )
    return


if __name__ == "__main__":
    app.run()
