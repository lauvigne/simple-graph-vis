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
    con = duckdb.connect(str(base_path / "local.duckdb"))
    return con


def write_model(con, model: dict[str, pd.DataFrame]) -> None:
    for table, frame in model.items():
        if not isinstance(frame, pd.DataFrame):
            continue
        con.register(f"{table}_df", frame)
        con.execute(f"CREATE OR REPLACE TABLE {table} AS SELECT * FROM {table}_df")
        con.unregister(f"{table}_df")


def reset_storage(base_dir: str | Path = "data") -> None:
    base_path = Path(base_dir).expanduser().resolve()
    for filename in ("local.duckdb", "local.duckdb.wal", "metadata.ducklake"):
        path = base_path / filename
        if path.exists():
            path.unlink()
    files_dir = base_path / "files"
    if files_dir.exists():
        shutil.rmtree(files_dir)


def read_table(con, table: str) -> pd.DataFrame:
    return con.execute(f"SELECT * FROM {table}").fetchdf()


def load_model(con) -> dict[str, pd.DataFrame]:
    tables = con.execute(
        """
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'main'
        ORDER BY table_name
        """
    ).fetchall()
    return {table_name: read_table(con, table_name) for (table_name,) in tables}


def storage_exists(base_dir: str | Path = "data") -> bool:
    base_path = Path(base_dir).expanduser().resolve()
    db_path = base_path / "local.duckdb"
    if not db_path.exists():
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
