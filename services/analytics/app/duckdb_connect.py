from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import duckdb

from app.config import get_settings


def create_duckdb_connection(*, database: str, read_only: bool = False) -> duckdb.DuckDBPyConnection:
    """Create and initialize a DuckDB connection used as analytics sidecar."""
    if database != ":memory:":
        Path(database).parent.mkdir(parents=True, exist_ok=True)
    connection = duckdb.connect(database=database, read_only=read_only)
    connection.execute("PRAGMA threads=4")
    return connection


@lru_cache(maxsize=1)
def get_duckdb_connection() -> duckdb.DuckDBPyConnection:
    settings = get_settings()
    return create_duckdb_connection(database=settings.duckdb_path, read_only=False)
