from __future__ import annotations

from typing import Any

import httpx


class CurrentMarketAdapter:
    """Optional adapter to enrich screen inputs with current prices."""

    def __init__(
        self,
        *,
        timeout_seconds: float = 10.0,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self._timeout_seconds = timeout_seconds
        self._transport = transport

    def get_current_prices(
        self,
        *,
        symbols: list[str],
        base_url: str,
    ) -> dict[str, float]:
        normalized = sorted({symbol.strip().upper() for symbol in symbols if symbol.strip()})
        if not normalized:
            return {}

        prices: dict[str, float] = {}
        try:
            with httpx.Client(
                base_url=base_url.rstrip("/"),
                timeout=self._timeout_seconds,
                transport=self._transport,
            ) as client:
                for symbol in normalized:
                    response = client.get(f"/current/{symbol}")
                    if response.status_code >= 400:
                        continue
                    payload: Any = response.json()
                    if not isinstance(payload, dict):
                        continue
                    price = payload.get("close")
                    if isinstance(price, int | float):
                        prices[symbol] = float(price)
        except httpx.HTTPError:
            return prices
        return prices
