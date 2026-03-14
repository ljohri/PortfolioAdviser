from __future__ import annotations

from dataclasses import dataclass

from app.repositories.tickers import TickerCreate, TickerRepository


@dataclass
class TickerServiceImpl:
    ticker_repository: TickerRepository

    def add_ticker(
        self,
        *,
        symbol: str,
        name: str | None = None,
        exchange: str | None = None,
        asset_type: str | None = None,
    ):
        payload = TickerCreate(
            symbol=symbol.upper(),
            name=name,
            exchange=exchange,
            asset_type=asset_type,
            active=True,
        )
        return self.ticker_repository.create_or_get(payload)

    def list_tickers(self):
        return self.ticker_repository.list_tickers()
