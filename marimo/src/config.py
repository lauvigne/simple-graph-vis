from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class FactColumnConfig:
    aliases: tuple[str, ...]
    role: str
    dtype: str = "string"
    required: bool = False
    allowed_values: tuple[str | int, ...] = field(default_factory=tuple)
    min_value: int | None = None


@dataclass(frozen=True)
class HierarchySheetConfig:
    sheet_names: tuple[str, ...]
    header_row: int
    path_columns: tuple[tuple[str, ...], ...]
    path_code_columns: tuple[tuple[str, ...], ...] = field(default_factory=tuple)
    source_path: str | None = None


@dataclass(frozen=True)
class MappingSheetConfig:
    sheet_names: tuple[str, ...]
    entity_value: str
    application_code_column: tuple[str, ...]
    application_column: tuple[str, ...]
    application_name_column: tuple[str, ...]
    target_path_columns: tuple[tuple[str, ...], ...]
    source_path: str | None = None


@dataclass(frozen=True)
class FactSheetConfig:
    sheet_names: tuple[str, ...]
    target_table: str
    header_row: int
    columns: tuple[FactColumnConfig, ...]
    source_path: str | None = None


@dataclass(frozen=True)
class ImportConfig:
    hierarchy_sheets: tuple[HierarchySheetConfig, ...]
    mapping_sheets: tuple[MappingSheetConfig, ...]
    fact_sheets: tuple[FactSheetConfig, ...] = field(default_factory=tuple)


ENTITY_SPECS = (
    ("E1", "Entity 1"),
    ("E2", "Entity 2"),
    ("E3", "Entity 3"),
    ("E4", "Entity 4"),
)


INCIDENTS_FACT_SHEET = FactSheetConfig(
    sheet_names=("Incidents",),
    target_table="fact_incidents",
    header_row=1,
    columns=(
        FactColumnConfig(aliases=("Application Code", "Code application"), role="application_code", dtype="string", required=True),
        FactColumnConfig(aliases=("Year", "Année", "Annee"), role="year", dtype="integer", required=True),
        FactColumnConfig(aliases=("Type", "Incident Type", "Incident type"), role="incident_type", dtype="integer", required=True, allowed_values=(1, 2)),
        FactColumnConfig(aliases=("Incident Count", "Nombre d'incidents", "Nombre incidents"), role="incident_count", dtype="integer", required=True, min_value=0),
    ),
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


INCIDENTS_ONLY_CONFIG = ImportConfig(
    hierarchy_sheets=tuple(),
    mapping_sheets=tuple(),
    fact_sheets=(INCIDENTS_FACT_SHEET,),
)
