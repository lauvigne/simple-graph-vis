from __future__ import annotations

from pathlib import Path

import pandas as pd

from .config import DEFAULT_CONFIG, ImportConfig
from .transformations import build_model


def load_workbook(path: str | Path, config: ImportConfig = DEFAULT_CONFIG) -> dict[str, pd.DataFrame]:
    workbook_path = Path(path)
    frames: dict[str, pd.DataFrame] = {}
    sheet_names = _configured_sheet_names(config)
    for sheet_name, header_row in sheet_names.items():
        frames[sheet_name] = pd.read_excel(workbook_path, sheet_name=sheet_name, header=header_row - 1, dtype=str).fillna("")
    return frames


def load_excel_model(path: str | Path, config: ImportConfig = DEFAULT_CONFIG) -> dict[str, pd.DataFrame]:
    return build_model(load_workbook(path, config), config)


def _configured_sheet_names(config: ImportConfig) -> dict[str, int]:
    names: dict[str, int] = {}
    for sheet in config.hierarchy_sheets:
        for name in sheet.sheet_names:
            names[name] = sheet.header_row
    for sheet in config.mapping_sheets:
        for name in sheet.sheet_names:
            names[name] = 1
    return names
