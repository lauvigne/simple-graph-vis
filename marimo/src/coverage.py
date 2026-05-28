from __future__ import annotations

import pandas as pd


def application_scopes(model: dict[str, pd.DataFrame]) -> pd.DataFrame:
    bridge = model["bridge_application_capability"]
    closure = model["capability_closure"]
    scopes = bridge.merge(closure, left_on="capability_code", right_on="ancestor_code", how="inner")
    return scopes[["application_code", "entity_code", "descendant_code"]].drop_duplicates()


def coverage_candidates(
    model: dict[str, pd.DataFrame],
    threshold: float = 0.8,
    entity: str | None = None,
    scope_mode: str = "all",
    limit: int = 5000,
) -> pd.DataFrame:
    scopes = application_scopes(model)
    if entity:
        covered_scopes = scopes[scopes["entity_code"] == entity]
    else:
        covered_scopes = scopes
    covered_sizes = covered_scopes.groupby(["application_code", "entity_code"]).size().reset_index(name="covered_count")
    covering_sizes = scopes.groupby(["application_code", "entity_code"]).size().reset_index(name="covering_count")
    overlaps = covered_scopes.merge(scopes, on="descendant_code", suffixes=("_covered", "_covering"))
    overlaps = overlaps[overlaps["application_code_covered"] != overlaps["application_code_covering"]]
    if scope_mode == "withinEntity":
        overlaps = overlaps[overlaps["entity_code_covered"] == overlaps["entity_code_covering"]]
    elif scope_mode == "crossEntity":
        overlaps = overlaps[overlaps["entity_code_covered"] != overlaps["entity_code_covering"]]
    counts = overlaps.groupby(
        ["application_code_covered", "entity_code_covered", "application_code_covering", "entity_code_covering"]
    ).size().reset_index(name="overlap_count")
    result = counts.merge(
        covered_sizes,
        left_on=["application_code_covered", "entity_code_covered"],
        right_on=["application_code", "entity_code"],
        how="left",
    ).drop(columns=["application_code", "entity_code"])
    result = result.merge(
        covering_sizes,
        left_on=["application_code_covering", "entity_code_covering"],
        right_on=["application_code", "entity_code"],
        how="left",
    ).drop(columns=["application_code", "entity_code"])
    result["coverage"] = result["overlap_count"] / result["covered_count"]
    result["type"] = result["coverage"].map(lambda value: "exact" if value == 1 else "near")
    result = result[(result["coverage"] == 1) | (result["coverage"] >= threshold)]
    return result.sort_values(["coverage", "application_code_covered"], ascending=[False, True]).head(limit)


def candidate_details(model: dict[str, pd.DataFrame], covered_app: str, covering_app: str) -> dict[str, pd.DataFrame]:
    scopes = application_scopes(model)
    capabilities = model["dim_business_capability"]
    covered = set(scopes.loc[scopes["application_code"] == covered_app, "descendant_code"])
    covering = set(scopes.loc[scopes["application_code"] == covering_app, "descendant_code"])
    return {
        "shared": capabilities[capabilities["code"].isin(covered & covering)],
        "missing": capabilities[capabilities["code"].isin(covered - covering)],
        "extra": capabilities[capabilities["code"].isin(covering - covered)],
    }
