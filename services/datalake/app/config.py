from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache


@dataclass(frozen=True)
class Settings:
    database_url: str
    tiingo_api_token: str | None
    tiingo_base_url: str
    app_env: str


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings(
        database_url=os.getenv(
            "DATABASE_URL",
            "postgresql+psycopg://stocklake:stocklake@localhost:5432/stocklake",
        ),
        tiingo_api_token=os.getenv("TIINGO_API_TOKEN"),
        tiingo_base_url=os.getenv("TIINGO_BASE_URL", "https://api.tiingo.com"),
        app_env=os.getenv("APP_ENV", "dev"),
    )
