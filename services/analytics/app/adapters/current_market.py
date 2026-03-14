from __future__ import annotations

from typing import Any

import httpx


class CurrentMarketAdapter:
    """Reads current snapshot prices from market-live style API."""

    def __init__(self, *, timeout_seconds: float = 5.0) -> None:
        self._timeout_seconds = timeout_seconds

    def get_current_prices(self, *, symbols: list[str], base_url: str) -> dict[str, float]:
        prices: dict[str, float] = {}
        if not symbols:
            return prices
        with httpx.Client(base_url=base_url.rstrip("/"), timeout=self._timeout_seconds) as client:
            for symbol in symbols:
                response = client.get(f"/current/{symbol}")
                if response.status_code >= 400:
                    continue
                payload: Any = response.json()
                if not isinstance(payload, dict):
                    continue
                close_value = payload.get("close")
                if close_value is None:
                    close_value = payload.get("price")
                if close_value is None:
                    continue
                prices[symbol] = float(close_value)
        return prices
