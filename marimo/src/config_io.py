from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from .config import (
    DEFAULT_CONFIG,
    FactColumnConfig,
    FactSheetConfig,
    HierarchySheetConfig,
    ImportConfig,
    MappingSheetConfig,
)


def load_import_config(path: str | Path) -> ImportConfig:
    config_path = Path(path).expanduser().resolve()
    data = json.loads(config_path.read_text(encoding="utf-8"))
    return import_config_from_dict(data, base_dir=config_path.parent)


def save_import_config(config: ImportConfig, path: str | Path) -> None:
    config_path = Path(path).expanduser().resolve()
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(json.dumps(import_config_to_dict(config), indent=2, ensure_ascii=False), encoding="utf-8")


def import_config_to_dict(config: ImportConfig) -> dict[str, Any]:
    return {
        "version": 1,
        "hierarchySheets": [_hierarchy_sheet_to_dict(sheet) for sheet in config.hierarchy_sheets],
        "mappingSheets": [_mapping_sheet_to_dict(sheet) for sheet in config.mapping_sheets],
        "factSheets": [_fact_sheet_to_dict(sheet) for sheet in config.fact_sheets],
    }


def import_config_from_dict(data: dict[str, Any], base_dir: str | Path | None = None) -> ImportConfig:
    base_path = Path(base_dir).expanduser().resolve() if base_dir is not None else None
    hierarchy_sheets = tuple(
        _hierarchy_sheet_from_dict(item, base_path)
        for item in data.get("hierarchySheets", [])
    )
    mapping_sheets = tuple(
        _mapping_sheet_from_dict(item, base_path)
        for item in data.get("mappingSheets", [])
    )
    fact_sheets = tuple(
        _fact_sheet_from_dict(item, base_path)
        for item in data.get("factSheets", [])
    )
    if not hierarchy_sheets and not mapping_sheets and not fact_sheets:
        return DEFAULT_CONFIG
    return ImportConfig(
        hierarchy_sheets=hierarchy_sheets,
        mapping_sheets=mapping_sheets,
        fact_sheets=fact_sheets,
    )


def _resolve_source_path(value: str | None, base_path: Path | None) -> str | None:
    if not value:
        return None
    source_path = Path(value).expanduser()
    if not source_path.is_absolute() and base_path is not None:
        source_path = (base_path / source_path).resolve()
    return str(source_path)


def _hierarchy_sheet_from_dict(item: dict[str, Any], base_path: Path | None) -> HierarchySheetConfig:
    return HierarchySheetConfig(
        sheet_names=tuple(item.get("sheetNames", [])),
        header_row=int(item.get("headerRow", 1)),
        path_columns=tuple(tuple(column) for column in item.get("pathColumns", [])),
        path_code_columns=tuple(tuple(column) for column in item.get("pathCodeColumns", [])),
        source_path=_resolve_source_path(item.get("sourcePath"), base_path),
    )


def _mapping_sheet_from_dict(item: dict[str, Any], base_path: Path | None) -> MappingSheetConfig:
    return MappingSheetConfig(
        sheet_names=tuple(item.get("sheetNames", [])),
        entity_value=str(item.get("entityValue", "")),
        application_code_column=tuple(item.get("applicationCodeColumn", [])),
        application_column=tuple(item.get("applicationColumn", [])),
        application_name_column=tuple(item.get("applicationNameColumn", [])),
        target_path_columns=tuple(tuple(column) for column in item.get("targetPathColumns", [])),
        source_path=_resolve_source_path(item.get("sourcePath"), base_path),
    )


def _fact_sheet_from_dict(item: dict[str, Any], base_path: Path | None) -> FactSheetConfig:
    return FactSheetConfig(
        sheet_names=tuple(item.get("sheetNames", [])),
        target_table=str(item.get("targetTable", "")),
        header_row=int(item.get("headerRow", 1)),
        columns=tuple(_fact_column_from_dict(column) for column in item.get("columns", [])),
        source_path=_resolve_source_path(item.get("sourcePath"), base_path),
    )


def _fact_column_from_dict(item: dict[str, Any]) -> FactColumnConfig:
    allowed_values = tuple(item.get("allowedValues", []))
    return FactColumnConfig(
        aliases=tuple(item.get("aliases", [])),
        role=str(item.get("role", "")),
        dtype=str(item.get("dtype", "string")),
        required=bool(item.get("required", False)),
        allowed_values=allowed_values,
        min_value=_optional_int(item.get("minValue")),
    )


def _hierarchy_sheet_to_dict(sheet: HierarchySheetConfig) -> dict[str, Any]:
    payload = asdict(sheet)
    payload["sheetNames"] = list(payload.pop("sheet_names"))
    payload["headerRow"] = payload.pop("header_row")
    payload["pathColumns"] = [list(column) for column in payload.pop("path_columns")]
    payload["pathCodeColumns"] = [list(column) for column in payload.pop("path_code_columns")]
    payload["sourcePath"] = payload.pop("source_path")
    return payload


def _mapping_sheet_to_dict(sheet: MappingSheetConfig) -> dict[str, Any]:
    payload = asdict(sheet)
    payload["sheetNames"] = list(payload.pop("sheet_names"))
    payload["entityValue"] = payload.pop("entity_value")
    payload["applicationCodeColumn"] = list(payload.pop("application_code_column"))
    payload["applicationColumn"] = list(payload.pop("application_column"))
    payload["applicationNameColumn"] = list(payload.pop("application_name_column"))
    payload["targetPathColumns"] = [list(column) for column in payload.pop("target_path_columns")]
    payload["sourcePath"] = payload.pop("source_path")
    return payload


def _fact_sheet_to_dict(sheet: FactSheetConfig) -> dict[str, Any]:
    payload = asdict(sheet)
    payload["sheetNames"] = list(payload.pop("sheet_names"))
    payload["targetTable"] = payload.pop("target_table")
    payload["headerRow"] = payload.pop("header_row")
    payload["columns"] = [_fact_column_to_dict(column) for column in sheet.columns]
    payload["sourcePath"] = payload.pop("source_path")
    return payload


def _fact_column_to_dict(column: FactColumnConfig) -> dict[str, Any]:
    payload = asdict(column)
    payload["aliases"] = list(payload.pop("aliases"))
    payload["role"] = payload.pop("role")
    payload["dtype"] = payload.pop("dtype")
    payload["required"] = payload.pop("required")
    payload["allowedValues"] = list(payload.pop("allowed_values"))
    payload["minValue"] = payload.pop("min_value")
    return payload


def _optional_int(value: Any) -> int | None:
    if value in (None, ""):
        return None
    return int(value)
