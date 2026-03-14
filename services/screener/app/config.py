from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache


@dataclass(frozen=True)
class Settings:
    app_env: str
    duckdb_path: str
    datalake_postgres_dsn: str | None
    market_live_base_url: str
    market_live_timeout_seconds: float


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings(
        app_env=os.getenv("APP_ENV", "dev"),
        duckdb_path=os.getenv("SCREENER_DUCKDB_PATH", ":memory:"),
        datalake_postgres_dsn=os.getenv("DATALAKE_POSTGRES_DSN"),
        market_live_base_url=os.getenv("MARKET_LIVE_BASE_URL", "http://localhost:8001"),
        market_live_timeout_seconds=float(os.getenv("MARKET_LIVE_TIMEOUT_SECONDS", "10")),
    )
