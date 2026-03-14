from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache


@dataclass(frozen=True)
class Settings:
    market_live_base_url: str
    market_live_timeout_seconds: float


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings(
        market_live_base_url=os.getenv("MARKET_LIVE_BASE_URL", "http://localhost:8001"),
        market_live_timeout_seconds=float(os.getenv("MARKET_LIVE_TIMEOUT_SECONDS", "10")),
    )
