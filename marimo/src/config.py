from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class HierarchySheetConfig:
    sheet_names: tuple[str, ...]
    header_row: int
    path_columns: tuple[tuple[str, ...], ...]
    path_code_columns: tuple[tuple[str, ...], ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class MappingSheetConfig:
    sheet_names: tuple[str, ...]
    entity_value: str
    application_code_column: tuple[str, ...]
    application_column: tuple[str, ...]
    application_name_column: tuple[str, ...]
    target_path_columns: tuple[tuple[str, ...], ...]


@dataclass(frozen=True)
class ImportConfig:
    hierarchy_sheets: tuple[HierarchySheetConfig, ...]
    mapping_sheets: tuple[MappingSheetConfig, ...]


ENTITY_SPECS = (
    ("E1", "Entity 1"),
    ("E2", "Entity 2"),
    ("E3", "Entity 3"),
    ("E4", "Entity 4"),
)


DEFAULT_CONFIG = ImportConfig(
    hierarchy_sheets=(
        HierarchySheetConfig(
            sheet_names=("BIAN Capabilities",),
            header_row=3,
            path_columns=(
                ("Business Capability (L1)",),
                ("Business Capability (L2)",),
                ("Business Capability (L3)",),
            ),
            path_code_columns=(
                tuple(),
                ("Business Capability (L2) long name",),
                ("Business Capability (L3) long name",),
            ),
        ),
    ),
    mapping_sheets=tuple(
        MappingSheetConfig(
            sheet_names=(f"{entity_code}-BCM",),
            entity_value=entity_name,
            application_code_column=("Application Code",),
            application_column=("Application Display Name",),
            application_name_column=("Application Name",),
            target_path_columns=(("BIAN L2",), ("BIAN L3",)),
        )
        for entity_code, entity_name in ENTITY_SPECS
    ),
)
