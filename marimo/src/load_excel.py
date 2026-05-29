from __future__ import annotations

from pathlib import Path

import pandas as pd

from .config import DEFAULT_CONFIG, ImportConfig
from .transformations import build_model, find_sheet_name


def load_workbook(path: str | Path, config: ImportConfig = DEFAULT_CONFIG) -> dict[str, pd.DataFrame]:
    workbook_path = Path(path)
    frames: dict[str, pd.DataFrame] = {}
    sheet_specs_by_source = _configured_sheet_specs(config, workbook_path)
    for source_path, sheet_specs in sheet_specs_by_source.items():
        excel_file = pd.ExcelFile(source_path)
        for sheet_spec in sheet_specs:
            sheet_name = find_sheet_name(excel_file.sheet_names, sheet_spec["aliases"])
            if not sheet_name:
                continue
            frames[_sheet_key(source_path, sheet_name)] = pd.read_excel(
                excel_file,
                sheet_name=sheet_name,
                header=sheet_spec["header_row"] - 1,
                dtype=str,
            ).fillna("")
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
    for sheet in config.fact_sheets:
        for name in sheet.sheet_names:
            names[name] = sheet.header_row
    return names


def _configured_sheet_specs(config: ImportConfig, workbook_path: Path) -> dict[Path, list[dict[str, object]]]:
    grouped: dict[Path, list[dict[str, object]]] = {}
    for sheet in config.hierarchy_sheets:
        source_path = _resolve_source_path(sheet.source_path, workbook_path)
        grouped.setdefault(source_path, []).append({"aliases": sheet.sheet_names, "header_row": sheet.header_row})
    for sheet in config.mapping_sheets:
        source_path = _resolve_source_path(sheet.source_path, workbook_path)
        grouped.setdefault(source_path, []).append({"aliases": sheet.sheet_names, "header_row": 1})
    for sheet in config.fact_sheets:
        source_path = _resolve_source_path(sheet.source_path, workbook_path)
        grouped.setdefault(source_path, []).append({"aliases": sheet.sheet_names, "header_row": sheet.header_row})
    return grouped


def _resolve_source_path(source_path: str | None, workbook_path: Path) -> Path:
    if not source_path:
        return workbook_path.expanduser().resolve()
    path = Path(source_path).expanduser()
    if not path.is_absolute():
        path = (workbook_path.parent / path).resolve()
    return path


def _sheet_key(source_path: Path, sheet_name: str) -> str:
    return f"{source_path.as_posix()}::{sheet_name}"
