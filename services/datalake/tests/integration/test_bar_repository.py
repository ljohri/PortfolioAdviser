from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import DailyBar
from app.repositories.bars import BarRepository, DailyBarUpsert
from app.repositories.tickers import TickerCreate, TickerRepository


@pytest.mark.integration
def test_bar_repository_idempotent_upsert(db_session: Session) -> None:
    ticker_repo = TickerRepository(db_session)
    ticker = ticker_repo.create_or_get(TickerCreate(symbol="AAPL"))
    db_session.flush()

    bar_repo = BarRepository(db_session)
    trading_date = date(2024, 1, 2)
    first = DailyBarUpsert(
        ticker_id=ticker.id,
        trading_date=trading_date,
        open_raw=Decimal("100"),
        high_raw=Decimal("110"),
        low_raw=Decimal("90"),
        close_raw=Decimal("105"),
        volume_raw=1000,
        open_adj=Decimal("99"),
        high_adj=Decimal("109"),
        low_adj=Decimal("89"),
        close_adj=Decimal("104"),
        volume_adj=1100,
        adj_factor=Decimal("1"),
        dividend_cash=Decimal("0"),
        split_factor=Decimal("1"),
        provider_payload={"source": "first"},
    )
    second = DailyBarUpsert(
        ticker_id=ticker.id,
        trading_date=trading_date,
        open_raw=Decimal("101"),
        high_raw=Decimal("111"),
        low_raw=Decimal("91"),
        close_raw=Decimal("106"),
        volume_raw=2000,
        open_adj=Decimal("100"),
        high_adj=Decimal("110"),
        low_adj=Decimal("90"),
        close_adj=Decimal("105"),
        volume_adj=2100,
        adj_factor=Decimal("1"),
        dividend_cash=Decimal("0"),
        split_factor=Decimal("1"),
        provider_payload={"source": "second"},
    )

    bar_repo.upsert_daily_bars([first])
    bar_repo.upsert_daily_bars([second])
    db_session.commit()

    count_statement = select(func.count(DailyBar.id))
    row_count = db_session.execute(count_statement).scalar_one()
    assert row_count == 1

    bars = bar_repo.list_by_symbol("AAPL")
    assert len(bars) == 1
    assert bars[0].close_raw == Decimal("106")
