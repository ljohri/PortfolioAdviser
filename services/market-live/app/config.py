from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache


@dataclass(frozen=True)
class Settings:
    tiingo_api_token: str | None
    tiingo_base_url: str
    app_env: str


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings(
        tiingo_api_token=os.getenv("TIINGO_API_TOKEN"),
        tiingo_base_url=os.getenv("TIINGO_BASE_URL", "https://api.tiingo.com"),
        app_env=os.getenv("APP_ENV", "dev"),
    )
