from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Any

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.db.models import DailyBar, Ticker
from app.repositories.impl.bars_sql import build_postgres_upsert_statement


@dataclass(frozen=True)
class DailyBarUpsert:
    ticker_id: int
    trading_date: date
    open_raw: Decimal | None
    high_raw: Decimal | None
    low_raw: Decimal | None
    close_raw: Decimal | None
    volume_raw: int | None
    open_adj: Decimal | None
    high_adj: Decimal | None
    low_adj: Decimal | None
    close_adj: Decimal | None
    volume_adj: int | None
    adj_factor: Decimal | None
    dividend_cash: Decimal | None
    split_factor: Decimal | None
    provider_payload: dict[str, Any] | None


class BarRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def list_by_symbol(
        self,
        symbol: str,
        *,
        start_date: date | None = None,
        end_date: date | None = None,
        limit: int = 500,
    ) -> list[DailyBar]:
        statement: Select[tuple[DailyBar]] = (
            select(DailyBar)
            .join(Ticker, Ticker.id == DailyBar.ticker_id)
            .where(Ticker.symbol == symbol.upper())
            .order_by(DailyBar.trading_date.asc())
            .limit(limit)
        )
        if start_date:
            statement = statement.where(DailyBar.trading_date >= start_date)
        if end_date:
            statement = statement.where(DailyBar.trading_date <= end_date)
        return list(self._session.execute(statement).scalars().all())

    def upsert_daily_bars(self, rows: list[DailyBarUpsert]) -> int:
        if not rows:
            return 0

        values = [row.__dict__ for row in rows]
        statement = build_postgres_upsert_statement(values)
        self._session.execute(statement)
        self._session.flush()
        return len(rows)
