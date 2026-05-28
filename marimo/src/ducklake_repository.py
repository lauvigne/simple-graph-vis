from __future__ import annotations

import shutil
from pathlib import Path

import pandas as pd


TABLES = (
    "dim_business_capability",
    "dim_application",
    "dim_entity",
    "bridge_application_capability",
    "capability_closure",
    "import_warnings",
)


def connect(base_dir: str | Path = "data"):
    try:
        import duckdb
    except ImportError as exc:
        raise RuntimeError("Install duckdb with `pip install -r requirements.txt`.") from exc

    base_path = Path(base_dir).expanduser().resolve()
    base_path.mkdir(parents=True, exist_ok=True)
    (base_path / "files").mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(base_path / "local.duckdb"))
    try:
        con.execute("INSTALL ducklake")
        con.execute("LOAD ducklake")
        metadata = (base_path / "metadata.ducklake").as_posix()
        data_path = (base_path / "files").as_posix()
        con.execute(f"ATTACH 'ducklake:{metadata}' AS lake (DATA_PATH '{data_path}')")
        con.execute("USE lake")
    except Exception:
        con.execute("USE main")
    return con


def write_model(con, model: dict[str, pd.DataFrame]) -> None:
    for table in TABLES:
        frame = model.get(table, pd.DataFrame())
        con.register(f"{table}_df", frame)
        con.execute(f"CREATE OR REPLACE TABLE {table} AS SELECT * FROM {table}_df")
        con.unregister(f"{table}_df")


def reset_storage(base_dir: str | Path = "data") -> None:
    base_path = Path(base_dir).expanduser().resolve()
    for filename in ("local.duckdb", "metadata.ducklake", "local.duckdb.wal"):
        path = base_path / filename
        if path.exists():
            path.unlink()
    files_dir = base_path / "files"
    if files_dir.exists():
        shutil.rmtree(files_dir)


def read_table(con, table: str) -> pd.DataFrame:
    if table not in TABLES:
        raise ValueError(f"Unknown table: {table}")
    return con.execute(f"SELECT * FROM {table}").fetchdf()


def load_model(con) -> dict[str, pd.DataFrame]:
    return {table: read_table(con, table) for table in TABLES}


def storage_exists(base_dir: str | Path = "data") -> bool:
    base_path = Path(base_dir).expanduser().resolve()
    db_path = base_path / "local.duckdb"
    metadata_path = base_path / "metadata.ducklake"
    if not db_path.exists() or not metadata_path.exists():
        return False
    try:
        con = connect(base_path)
    except Exception:
        return False
    try:
        existing = {
            row[0]
            for row in con.execute(
                "SELECT table_name FROM information_schema.tables WHERE table_schema = 'main'"
            ).fetchall()
        }
        return set(TABLES).issubset(existing)
    finally:
        con.close()
