from __future__ import annotations

from app.services.impl.ticker_logic import TickerServiceImpl


class TickerService:
    """Thin facade delegating ticker logic to impl module."""

    def __init__(self, impl: TickerServiceImpl) -> None:
        self._impl = impl

    def add_ticker(self, **kwargs):
        return self._impl.add_ticker(**kwargs)

    def list_tickers(self):
        return self._impl.list_tickers()
