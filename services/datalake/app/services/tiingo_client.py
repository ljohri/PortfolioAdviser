from __future__ import annotations

from datetime import date
from typing import Any

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import Settings


class TiingoClient:
    def __init__(self, settings: Settings, timeout_seconds: float = 30.0) -> None:
        self._settings = settings
        self._timeout_seconds = timeout_seconds

    @retry(wait=wait_exponential(multiplier=0.5, min=0.5, max=8), stop=stop_after_attempt(3), reraise=True)
    async def get_eod_bars(
        self,
        symbol: str,
        *,
        start_date: date,
        end_date: date,
    ) -> list[dict[str, Any]]:
        params = {
            "startDate": start_date.isoformat(),
            "endDate": end_date.isoformat(),
            "resampleFreq": "daily",
            "token": self._settings.tiingo_api_token,
        }
        url = f"{self._settings.tiingo_base_url}/tiingo/daily/{symbol.upper()}/prices"

        async with httpx.AsyncClient(timeout=self._timeout_seconds) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            payload = response.json()
            if not isinstance(payload, list):
                return []
            return [item for item in payload if isinstance(item, dict)]
