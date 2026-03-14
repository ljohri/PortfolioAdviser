from __future__ import annotations

from datetime import date
from typing import Any

from app.services.impl.stocklake_logic import StocklakeServiceImpl


class StocklakeService:
    """Facade exposing stocklake operations for external adapters (MCP/API)."""

    def __init__(self, impl: StocklakeServiceImpl) -> None:
        self._impl = impl

    def add_ticker(self, *, symbol: str, exchange: str | None = None) -> dict[str, Any]:
        return self._impl.add_ticker(symbol=symbol, exchange=exchange)

    def list_tickers(self) -> list[dict[str, Any]]:
        return self._impl.list_tickers()

    def get_history(self, *, symbol: str, start: date, end: date) -> list[dict[str, Any]]:
        return self._impl.get_history(symbol=symbol, start=start, end=end)

    async def backfill_ticker(
        self,
        *,
        symbol: str,
        start: date | None = None,
        end: date | None = None,
    ) -> dict[str, Any]:
        return await self._impl.backfill_ticker(symbol=symbol, start=start, end=end)

    def list_missing_ranges(self, *, symbol: str) -> list[dict[str, str]]:
        return self._impl.list_missing_ranges(symbol=symbol)

    async def run_daily_update(self) -> dict[str, Any]:
        return await self._impl.run_daily_update()
