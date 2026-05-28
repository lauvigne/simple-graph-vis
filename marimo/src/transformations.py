from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Iterable
import unicodedata

import pandas as pd

from .config import ImportConfig, MappingSheetConfig


@dataclass(frozen=True)
class ParsedCapability:
    raw_value: str
    code: str
    labels: tuple[str, ...]
    level: int | None


def clean_text(value: object) -> str:
    if value is None or pd.isna(value):
        return ""
    return re.sub(r"\s+", " ", "" if value is None else str(value)).strip()


def normalize_text(value: object) -> str:
    text = unicodedata.normalize("NFKD", clean_text(value))
    text = "".join(char for char in text if not unicodedata.combining(char))
    return text.lower()


def normalize_path(labels: Iterable[str]) -> str:
    return " / ".join(normalize_text(label) for label in labels if clean_text(label))


def match_header(headers: Iterable[str], aliases: Iterable[str]) -> str | None:
    normalized_headers = [(header, normalize_text(header)) for header in headers]
    normalized_aliases = [normalize_text(alias) for alias in aliases if clean_text(alias)]
    for alias in normalized_aliases:
        for header, normalized_header in normalized_headers:
            if normalized_header == alias:
                return header
    for alias in normalized_aliases:
        for header, normalized_header in normalized_headers:
            if alias in normalized_header:
                return header
    return None


def find_sheet_name(sheet_names: Iterable[str], aliases: Iterable[str]) -> str | None:
    return match_header(sheet_names, aliases)


def extract_leading_code(value: object) -> str:
    match = re.match(r"^(\d+(?:\.\d+)*)\s*(?:-|\s|$)", clean_text(value))
    return match.group(1) if match else ""


def code_at_level(code: str, level_index: int) -> str:
    parts = [part for part in clean_text(code).split(".") if part]
    if len(parts) <= level_index:
        return ""
    return ".".join(parts[: level_index + 1])


def strip_leading_code(value: object) -> str:
    return re.sub(r"^\d+(?:\.\d+)*\s*(?:-\s*)?", "", clean_text(value)).strip()


def split_values_by_code(value: object, depth: int) -> list[str]:
    text = clean_text(value)
    if not text:
        return []
    code_pattern = r"\d+\.\d+" if depth == 2 else rf"\d+\.\d+(?:\.\d+){{{depth - 2}}}"
    matches = [
        match.start(2)
        for match in re.finditer(rf"(^|[^\d.])({code_pattern})(?![\d.])", text)
    ]
    if not matches:
        return []
    values = []
    for index, start in enumerate(matches):
        end = matches[index + 1] if index + 1 < len(matches) else len(text)
        values.append(clean_text(re.sub(r"^[,;\s]+|[,;\s]+$", "", text[start:end])))
    return [value for value in values if value]


def split_cell_values(value: object, code_depth: int | None = None) -> list[str]:
    if code_depth:
        by_code = split_values_by_code(value, code_depth)
        if by_code:
            return by_code
    return [clean_text(part) for part in str(value or "").split(",") if clean_text(part)]


def split_path_labels(value: str) -> tuple[str, ...]:
    if "/" not in value:
        return (clean_text(value),) if clean_text(value) else tuple()
    return tuple(clean_text(part) for part in re.split(r"\s*/\s*", value) if clean_text(part))


def parse_capability_value(value: object) -> ParsedCapability | None:
    raw_value = clean_text(value)
    if not raw_value:
        return None
    code = extract_leading_code(raw_value)
    labels = split_path_labels(strip_leading_code(raw_value))
    level = len(code.split(".")) if code else None
    return ParsedCapability(raw_value=raw_value, code=code, labels=labels, level=level)


def expected_code_depth(header: str | None, aliases: Iterable[str]) -> int | None:
    candidates = [normalize_text(header or ""), *(normalize_text(alias) for alias in aliases)]
    if any(re.search(r"\b(l3|level 3|niveau 3)\b", value) for value in candidates):
        return 3
    if any(re.search(r"\b(l2|level 2|niveau 2)\b", value) for value in candidates):
        return 2
    return None


def build_capability_tables(workbook: dict[str, pd.DataFrame], config: ImportConfig) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows: dict[str, dict[str, object]] = {}
    warnings: list[dict[str, object]] = []
    path_index: dict[str, str] = {}

    for sheet_config in config.hierarchy_sheets:
        sheet_name = find_sheet_name(workbook.keys(), sheet_config.sheet_names)
        if not sheet_name:
            warnings.append(_warning("error", "", 0, "Hierarchy sheet not found", ", ".join(sheet_config.sheet_names)))
            continue
        frame = workbook[sheet_name]
        path_headers = [match_header(frame.columns, aliases) for aliases in sheet_config.path_columns]
        code_headers = [match_header(frame.columns, aliases) for aliases in sheet_config.path_code_columns]
        for row_index, row in frame.iterrows():
            labels = [clean_text(row[header]) for header in path_headers if header and clean_text(row[header])]
            deepest_code = _deepest_code(row, code_headers)
            parent_code = ""
            for level_index, label in enumerate(labels):
                code = code_at_level(deepest_code, level_index)
                path_labels = labels[: level_index + 1]
                stable_code = code or f"path:{normalize_path(path_labels)}"
                rows.setdefault(
                    stable_code,
                    {
                        "code": stable_code,
                        "level": level_index + 1,
                        "label": label,
                        "long_name": " / ".join(path_labels),
                        "parent_code": parent_code,
                        **_path_columns(path_labels),
                    },
                )
                path_index[normalize_path(path_labels)] = stable_code
                parent_code = stable_code
    frame = pd.DataFrame(rows.values(), columns=_capability_columns())
    frame.attrs["path_index"] = path_index
    return frame, pd.DataFrame(warnings, columns=_warning_columns())


def build_mapping_tables(
    workbook: dict[str, pd.DataFrame],
    config: ImportConfig,
    capabilities: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    applications: dict[str, dict[str, object]] = {}
    entities: dict[str, dict[str, object]] = {}
    bridges: list[dict[str, object]] = []
    warnings: list[dict[str, object]] = []
    capability_codes = set(capabilities["code"].dropna().astype(str))
    path_index = dict(capabilities.attrs.get("path_index", {}))

    for sheet_config in config.mapping_sheets:
        sheet_name = find_sheet_name(workbook.keys(), sheet_config.sheet_names)
        if not sheet_name:
            warnings.append(_warning("warning", "", 0, "Mapping sheet not found", ", ".join(sheet_config.sheet_names)))
            continue
        _extract_mapping_sheet(
            workbook[sheet_name],
            sheet_name,
            sheet_config,
            applications,
            entities,
            bridges,
            warnings,
            capability_codes,
            path_index,
        )
    return (
        pd.DataFrame(applications.values(), columns=["application_code", "application_name", "display_name", "entity_code"]),
        pd.DataFrame(entities.values(), columns=["entity_code", "label"]),
        pd.DataFrame(bridges, columns=["application_code", "entity_code", "capability_code", "mapped_level", "source_sheet", "source_row"]),
        pd.DataFrame(warnings, columns=_warning_columns()),
    )


def build_capability_closure(capabilities: pd.DataFrame) -> pd.DataFrame:
    parent_by_code = dict(zip(capabilities["code"], capabilities["parent_code"]))
    rows = []
    for code in capabilities["code"].dropna().astype(str):
        rows.append({"ancestor_code": code, "descendant_code": code, "depth": 0})
        depth = 1
        parent = parent_by_code.get(code)
        while parent:
            rows.append({"ancestor_code": parent, "descendant_code": code, "depth": depth})
            parent = parent_by_code.get(parent)
            depth += 1
    return pd.DataFrame(rows, columns=["ancestor_code", "descendant_code", "depth"])


def build_model(workbook: dict[str, pd.DataFrame], config: ImportConfig) -> dict[str, pd.DataFrame]:
    capabilities, hierarchy_warnings = build_capability_tables(workbook, config)
    applications, entities, bridges, mapping_warnings = build_mapping_tables(workbook, config, capabilities)
    closure = build_capability_closure(capabilities)
    warnings = pd.concat([hierarchy_warnings, mapping_warnings], ignore_index=True)
    return {
        "dim_business_capability": capabilities,
        "dim_application": applications,
        "dim_entity": entities,
        "bridge_application_capability": bridges,
        "capability_closure": closure,
        "import_warnings": warnings,
    }


def _extract_mapping_sheet(
    frame: pd.DataFrame,
    sheet_name: str,
    sheet_config: MappingSheetConfig,
    applications: dict[str, dict[str, object]],
    entities: dict[str, dict[str, object]],
    bridges: list[dict[str, object]],
    warnings: list[dict[str, object]],
    capability_codes: set[str],
    path_index: dict[str, str],
) -> None:
    app_code_header = match_header(frame.columns, sheet_config.application_code_column)
    app_header = match_header(frame.columns, sheet_config.application_column)
    app_name_header = match_header(frame.columns, sheet_config.application_name_column)
    target_specs = [
        (match_header(frame.columns, aliases), expected_code_depth(match_header(frame.columns, aliases), aliases))
        for aliases in sheet_config.target_path_columns
    ]
    for index, row in frame.iterrows():
        source_row = int(index) + 2
        application_code = clean_text(row[app_code_header]) if app_code_header else ""
        display_name = clean_text(row[app_header]) if app_header else application_code
        application_name = clean_text(row[app_name_header]) if app_name_header else display_name
        if not application_code and not display_name:
            continue
        application_code = application_code or display_name
        entity_code = sheet_config.entity_value
        entities.setdefault(entity_code, {"entity_code": entity_code, "label": entity_code})
        applications.setdefault(
            application_code,
            {
                "application_code": application_code,
                "application_name": application_name,
                "display_name": display_name,
                "entity_code": entity_code,
            },
        )
        for header, code_depth in target_specs:
            if not header:
                continue
            for cell_value in split_cell_values(row[header], code_depth):
                parsed = parse_capability_value(cell_value)
                if not parsed:
                    continue
                capability_code = _resolve_capability(parsed, capability_codes, path_index)
                if not capability_code:
                    warnings.append(_warning("warning", sheet_name, source_row, "Capability mapping not found", parsed.raw_value))
                    continue
                bridges.append(
                    {
                        "application_code": application_code,
                        "entity_code": entity_code,
                        "capability_code": capability_code,
                        "mapped_level": parsed.level,
                        "source_sheet": sheet_name,
                        "source_row": source_row,
                    }
                )


def _resolve_capability(parsed: ParsedCapability, capability_codes: set[str], path_index: dict[str, str]) -> str:
    if parsed.code and parsed.code in capability_codes:
        return parsed.code
    return path_index.get(normalize_path(parsed.labels), "")


def _deepest_code(row: pd.Series, code_headers: list[str | None]) -> str:
    for header in reversed(code_headers):
        if header:
            code = extract_leading_code(row[header])
            if code:
                return code
    return ""


def _path_columns(path_labels: list[str]) -> dict[str, str]:
    values = {f"path_l{index}": "" for index in range(1, 6)}
    for index, label in enumerate(path_labels[:5], start=1):
        values[f"path_l{index}"] = label
    return values


def _capability_columns() -> list[str]:
    return ["code", "level", "label", "long_name", "parent_code", "path_l1", "path_l2", "path_l3", "path_l4", "path_l5"]


def _warning(severity: str, source_sheet: str, source_row: int, message: str, raw_value: str) -> dict[str, object]:
    return {
        "severity": severity,
        "source_sheet": source_sheet,
        "source_row": source_row,
        "message": message,
        "raw_value": raw_value,
    }


def _warning_columns() -> list[str]:
    return ["severity", "source_sheet", "source_row", "message", "raw_value"]
