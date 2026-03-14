from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Ticker, TickerSyncState


@dataclass(frozen=True)
class TickerCreate:
    symbol: str
    name: str | None = None
    exchange: str | None = None
    asset_type: str | None = None
    active: bool = True


class TickerRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_symbol(self, symbol: str) -> Ticker | None:
        statement = select(Ticker).where(Ticker.symbol == symbol.upper())
        return self._session.execute(statement).scalar_one_or_none()

    def list_tickers(self) -> list[Ticker]:
        statement = select(Ticker).order_by(Ticker.symbol.asc())
        return list(self._session.execute(statement).scalars().all())

    def create_or_get(self, payload: TickerCreate) -> Ticker:
        existing = self.get_by_symbol(payload.symbol)
        if existing:
            return existing

        ticker = Ticker(
            symbol=payload.symbol.upper(),
            name=payload.name,
            exchange=payload.exchange,
            asset_type=payload.asset_type,
            active=payload.active,
        )
        self._session.add(ticker)
        self._session.flush()
        return ticker

    def upsert_sync_state(
        self,
        *,
        ticker_id: int,
        status: str,
        last_attempted_date: date | None = None,
        last_successful_date: date | None = None,
        message: str | None = None,
    ) -> TickerSyncState:
        statement = select(TickerSyncState).where(TickerSyncState.ticker_id == ticker_id)
        state = self._session.execute(statement).scalar_one_or_none()
        if state is None:
            state = TickerSyncState(ticker_id=ticker_id, status=status)
            self._session.add(state)

        state.status = status
        state.last_attempted_date = last_attempted_date
        state.last_successful_date = last_successful_date
        state.message = message
        self._session.flush()
        return state
