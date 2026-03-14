from __future__ import annotations

from datetime import date

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.repositories.bars import BarRepository
from app.repositories.tickers import TickerCreate, TickerRepository
from app.services.impl.tiingo_mapping import map_tiingo_payload_to_upsert
from app.services.tiingo_client import TiingoClient
from tests.factories import tiingo_bar_payload


def test_get_bars_for_symbol(client: TestClient, db_session: Session) -> None:
    ticker_repo = TickerRepository(db_session)
    ticker = ticker_repo.create_or_get(TickerCreate(symbol="AAPL"))
    db_session.flush()

    bar_repo = BarRepository(db_session)
    payload = tiingo_bar_payload(trading_date=date(2024, 1, 2))
    bar_repo.upsert_daily_bars(
        [
            map_tiingo_payload_to_upsert(ticker_id=ticker.id, payload_item=payload)
        ]
    )
    db_session.commit()

    response = client.get("/bars/AAPL")
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["symbol"] == "AAPL"
    assert body[0]["trading_date"] == "2024-01-02"


def test_backfill_endpoint(client: TestClient, db_session: Session, monkeypatch) -> None:
    ticker_repo = TickerRepository(db_session)
    ticker_repo.create_or_get(TickerCreate(symbol="AAPL"))
    db_session.commit()

    async def fake_get_eod_bars(self, symbol: str, *, start_date: date, end_date: date):
        assert symbol == "AAPL"
        return [
            tiingo_bar_payload(trading_date=start_date),
            tiingo_bar_payload(trading_date=end_date, close_raw=111.0),
        ]

    monkeypatch.setattr(TiingoClient, "get_eod_bars", fake_get_eod_bars)

    response = client.post(
        "/bars/backfill",
        json={
            "symbol": "AAPL",
            "start_date": "2024-01-01",
            "end_date": "2024-01-02",
            "chunk_days": 365,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["symbol"] == "AAPL"
    assert body["rows_written"] == 2

    bars_response = client.get("/bars/AAPL")
    assert bars_response.status_code == 200
    assert len(bars_response.json()) == 2
