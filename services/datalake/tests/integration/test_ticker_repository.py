from __future__ import annotations

import pytest
from sqlalchemy.orm import Session

from app.repositories.tickers import TickerCreate, TickerRepository


@pytest.mark.integration
def test_ticker_repository_create_and_list(db_session: Session) -> None:
    repo = TickerRepository(db_session)
    ticker = repo.create_or_get(TickerCreate(symbol="AAPL", name="Apple Inc.", exchange="NASDAQ", asset_type="stock"))
    db_session.commit()

    listed = repo.list_tickers()
    assert ticker.id is not None
    assert [item.symbol for item in listed] == ["AAPL"]


@pytest.mark.integration
def test_ticker_repository_create_is_idempotent_by_symbol(db_session: Session) -> None:
    repo = TickerRepository(db_session)
    first = repo.create_or_get(TickerCreate(symbol="MSFT"))
    second = repo.create_or_get(TickerCreate(symbol="msft"))
    db_session.commit()

    assert first.id == second.id
