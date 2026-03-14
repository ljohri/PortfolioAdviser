from __future__ import annotations

from datetime import date

import pytest

from app.repositories.bars import BarRepository
from app.repositories.tickers import TickerCreate, TickerRepository
from app.services.impl.tiingo_mapping import map_tiingo_payload_to_upsert
from app.services.tiingo_client import TiingoClient
from mcp_stocklake.tools import StocklakeTools
from sqlalchemy.orm import Session


@pytest.mark.integration
def test_add_and_list_tickers_use_real_datalake_logic(stocklake_tools: StocklakeTools) -> None:
    created = stocklake_tools.add_ticker("aapl", exchange="NASDAQ")
    listed = stocklake_tools.list_tickers()

    assert created["symbol"] == "AAPL"
    assert created["exchange"] == "NASDAQ"
    assert [item["symbol"] for item in listed] == ["AAPL"]


@pytest.mark.integration
def test_get_history_reads_from_canonical_bars(
    stocklake_tools: StocklakeTools,
    db_session: Session,
    tiingo_payload_factory,
) -> None:
    ticker_repo = TickerRepository(db_session)
    ticker = ticker_repo.create_or_get(TickerCreate(symbol="AAPL"))
    db_session.flush()

    bar_repo = BarRepository(db_session)
    bar_repo.upsert_daily_bars(
        [
            map_tiingo_payload_to_upsert(
                ticker_id=ticker.id,
                payload_item=tiingo_payload_factory(trading_date=date(2024, 1, 2), close=123.0),
            )
        ]
    )
    db_session.commit()

    history = stocklake_tools.get_history("AAPL", "2024-01-01", "2024-01-03")
    assert len(history) == 1
    assert history[0]["symbol"] == "AAPL"
    assert history[0]["trading_date"] == "2024-01-02"
    assert history[0]["close_raw"] == 123.0


@pytest.mark.integration
@pytest.mark.asyncio
async def test_backfill_and_missing_ranges_with_real_service_logic(
    stocklake_tools: StocklakeTools,
    tiingo_payload_factory,
    monkeypatch,
) -> None:
    stocklake_tools.add_ticker("AAPL", exchange="NASDAQ")

    async def fake_get_eod_bars(self, symbol: str, *, start_date: date, end_date: date):
        assert symbol == "AAPL"
        return [
            tiingo_payload_factory(trading_date=start_date, close=111.0),
            tiingo_payload_factory(trading_date=end_date, close=112.0),
        ]

    monkeypatch.setattr(TiingoClient, "get_eod_bars", fake_get_eod_bars)

    result = await stocklake_tools.backfill_ticker("AAPL", start="2024-01-01", end="2024-01-02")
    assert result["symbol"] == "AAPL"
    assert result["rows_written"] == 2

    missing = stocklake_tools.list_missing_ranges("AAPL")
    assert isinstance(missing, list)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_run_daily_update_processes_active_tickers(
    stocklake_tools: StocklakeTools,
    tiingo_payload_factory,
    monkeypatch,
) -> None:
    stocklake_tools.add_ticker("AAPL")
    stocklake_tools.add_ticker("MSFT")

    async def fake_get_eod_bars(self, symbol: str, *, start_date: date, end_date: date):
        return [tiingo_payload_factory(trading_date=start_date, close=100.0)]

    monkeypatch.setattr(TiingoClient, "get_eod_bars", fake_get_eod_bars)

    summary = await stocklake_tools.run_daily_update()
    assert summary["tickers_processed"] == 2
    assert len(summary["results"]) == 2

