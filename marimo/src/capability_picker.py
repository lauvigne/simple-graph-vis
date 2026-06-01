from __future__ import annotations

import pandas as pd


def capability_catalog(model: dict[str, pd.DataFrame]) -> pd.DataFrame:
    frame = model.get("dim_business_capability", pd.DataFrame()).copy()
    if frame.empty:
        return pd.DataFrame(
            columns=[
                "code",
                "label",
                "long_name",
                "path_l1",
                "path_l2",
                "path_l3",
                "path_l4",
                "path_l5",
                "l1_code",
                "l2_code",
                "leaf_code",
                "l1_label",
                "l2_label",
                "leaf_label",
                "search_blob",
            ]
        )

    frame["code"] = frame["code"].fillna("").astype(str).str.strip()
    frame["label"] = frame["label"].fillna("").astype(str).str.strip()
    frame["long_name"] = frame["long_name"].fillna("").astype(str).str.strip()
    for column in ["path_l1", "path_l2", "path_l3", "path_l4", "path_l5"]:
        if column not in frame.columns:
            frame[column] = ""
        frame[column] = frame[column].fillna("").astype(str).str.strip()

    frame["l1_code"] = frame["code"].map(lambda code: _prefix_code(code, 1))
    frame["l2_code"] = frame["code"].map(lambda code: _prefix_code(code, 2))
    frame["leaf_code"] = frame["code"]
    frame["l1_label"] = frame.apply(lambda row: _display_level(row["l1_code"], row["path_l1"]), axis=1)
    frame["l2_label"] = frame.apply(lambda row: _display_level(row["l2_code"], row["path_l2"]), axis=1)
    frame["leaf_label"] = frame.apply(_display_leaf, axis=1)
    frame["search_blob"] = frame[
        ["code", "label", "long_name", "path_l1", "path_l2", "path_l3", "path_l4", "path_l5"]
    ].agg(" ".join, axis=1).str.lower()

    return frame.sort_values(["l1_code", "l2_code", "leaf_code"]).reset_index(drop=True)


def filter_catalog(
    catalog: pd.DataFrame,
    search: str = "",
    l1_code: str = "",
    l2_code: str = "",
) -> pd.DataFrame:
    frame = catalog
    if search.strip():
        query = search.strip().lower()
        frame = frame[frame["search_blob"].str.contains(query, na=False)]
    if l1_code:
        frame = frame[frame["l1_code"] == l1_code]
    if l2_code:
        frame = frame[frame["l2_code"] == l2_code]
    return frame.reset_index(drop=True)


def level1_options(catalog: pd.DataFrame, search: str = "") -> dict[str, str]:
    frame = filter_catalog(catalog, search=search)
    options = _option_map(frame, value_column="l1_code", label_column="l1_label")
    return {"Tous les niveaux 1": "", **options}


def level2_options(catalog: pd.DataFrame, search: str = "", l1_code: str = "") -> dict[str, str]:
    frame = filter_catalog(catalog, search=search, l1_code=l1_code)
    frame = frame[frame["l2_code"].astype(str).str.strip() != ""]
    options = _option_map(frame, value_column="l2_code", label_column="l2_label")
    return {"Tous les niveaux 2": "", **options}


def leaf_options(catalog: pd.DataFrame, search: str = "", l1_code: str = "", l2_code: str = "") -> dict[str, str]:
    frame = filter_catalog(catalog, search=search, l1_code=l1_code, l2_code=l2_code)
    frame = frame[frame["leaf_code"].astype(str).str.strip() != ""]
    options = _option_map(frame, value_column="leaf_code", label_column="leaf_label")
    return options


def selected_leaf_labels(catalog: pd.DataFrame, selected_codes: list[str]) -> list[str]:
    if not selected_codes:
        return []
    frame = catalog[catalog["leaf_code"].isin(selected_codes)][["leaf_code", "leaf_label"]].drop_duplicates()
    lookup = dict(zip(frame["leaf_code"], frame["leaf_label"]))
    return [lookup.get(code, code) for code in selected_codes]


def _option_map(frame: pd.DataFrame, value_column: str, label_column: str) -> dict[str, str]:
    if frame.empty:
        return {}
    subset = frame[[value_column, label_column]].drop_duplicates().sort_values([value_column, label_column])
    return {str(row[label_column]): str(row[value_column]) for _, row in subset.iterrows()}


def _prefix_code(code: object, depth: int) -> str:
    parts = [part.strip() for part in str(code or "").split(".") if part.strip()]
    if not parts:
        return ""
    return ".".join(parts[:depth])


def _display_level(code: object, label: object) -> str:
    code_text = str(code or "").strip()
    label_text = str(label or "").strip()
    if code_text and label_text:
        return f"{code_text} - {label_text}"
    return code_text or label_text or ""


def _display_leaf(row: pd.Series) -> str:
    code_text = str(row.get("leaf_code") or "").strip()
    for field in ("path_l3", "path_l2", "label", "long_name"):
        label_text = str(row.get(field) or "").strip()
        if code_text and label_text:
            return f"{code_text} - {label_text}"
        if label_text and not code_text:
            return label_text
    return code_text
