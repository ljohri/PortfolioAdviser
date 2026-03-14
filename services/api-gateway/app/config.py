from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache


@dataclass(frozen=True)
class Settings:
    datalake_base_url: str
    datalake_timeout_seconds: float
    market_live_base_url: str
    market_live_timeout_seconds: float
    app_env: str


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings(
        datalake_base_url=os.getenv("DATALAKE_BASE_URL", "http://localhost:8000"),
        datalake_timeout_seconds=float(os.getenv("DATALAKE_TIMEOUT_SECONDS", "10")),
        market_live_base_url=os.getenv("MARKET_LIVE_BASE_URL", "http://localhost:8001"),
        market_live_timeout_seconds=float(os.getenv("MARKET_LIVE_TIMEOUT_SECONDS", "10")),
        app_env=os.getenv("APP_ENV", "dev"),
    )
