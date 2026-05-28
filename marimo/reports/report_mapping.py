from __future__ import annotations

import pandas as pd

from src.coverage import coverage_candidates, candidate_details


def query_candidates(
    model: dict[str, pd.DataFrame],
    threshold: float,
    entity: str | None,
    scope_mode: str = "all",
) -> pd.DataFrame:
    return coverage_candidates(model, threshold=threshold, entity=entity or None, scope_mode=scope_mode)


def query_candidate_details(model: dict[str, pd.DataFrame], covered_app: str, covering_app: str) -> dict[str, pd.DataFrame]:
    return candidate_details(model, covered_app, covering_app)
