from __future__ import annotations

from datetime import date

import pytest

from app.errors import GatewayError, UpstreamHttpError
from app.models import BackfillRequest, TickerCreateRequest
from app.service import GatewayService


class _FakeDatalakeClient:
    def __init__(self) -> None:
        self.tickers = [{"id": 1, "symbol": "AAPL", "name": None, "exchange": None, "asset_type": None, "active": True}]
        self.history = []
        self.backfill_response = {"symbol": "AAPL", "ranges_processed": 1, "rows_written": 2}
        self.raise_on_backfill: UpstreamHttpError | None = None

    async def list_tickers(self):
        return self.tickers

    async def create_ticker(self, request: TickerCreateRequest):
        return {"id": 2, "symbol": request.symbol.upper(), "name": request.name, "exchange": request.exchange, "asset_type": request.asset_type, "active": True}

    async def list_history(self, *, symbol: str, start_date: date | None, end_date: date | None, limit: int):
        return self.history

    async def backfill_history(self, request: BackfillRequest):
        if self.raise_on_backfill is not None:
            raise self.raise_on_backfill
        return self.backfill_response


class _FakeMarketLiveClient:
    def __init__(self) -> None:
        self.current = {
            "symbol": "AAPL",
            "trading_date": "2024-01-03",
            "open_raw": "100.0",
            "high_raw": "110.0",
            "low_raw": "95.0",
            "close_raw": "105.0",
            "volume_raw": 1_000_000,
            "open_adj": "99.0",
            "high_adj": "109.0",
            "low_adj": "94.0",
            "close_adj": "104.0",
            "volume_adj": 1_100_000,
        }
        self.raise_on_current: UpstreamHttpError | None = None

    async def get_current(self, *, symbol: str):
        if self.raise_on_current is not None:
            raise self.raise_on_current
        return self.current


@pytest.mark.asyncio
async def test_get_history_returns_ticker_not_found_for_unknown_symbol() -> None:
    service = GatewayService(datalake_client=_FakeDatalakeClient(), market_live_client=_FakeMarketLiveClient())  # type: ignore[arg-type]

    with pytest.raises(GatewayError) as exc_info:
        await service.get_history(symbol="MSFT", start_date=None, end_date=None, limit=50)

    assert exc_info.value.status_code == 404
    assert exc_info.value.code == "ticker_not_found"


@pytest.mark.asyncio
async def test_backfill_maps_upstream_not_found_to_normalized_error() -> None:
    datalake_client = _FakeDatalakeClient()
    datalake_client.raise_on_backfill = UpstreamHttpError(status_code=404, detail="ticker not found: AAPL")
    service = GatewayService(datalake_client=datalake_client, market_live_client=_FakeMarketLiveClient())  # type: ignore[arg-type]

    with pytest.raises(GatewayError) as exc_info:
        await service.backfill_history(
            BackfillRequest(
                symbol="AAPL",
                start_date=date(2024, 1, 1),
                end_date=date(2024, 1, 2),
                chunk_days=365,
            )
        )

    assert exc_info.value.status_code == 404
    assert exc_info.value.code == "ticker_not_found"


@pytest.mark.asyncio
async def test_backfill_success_response_maps_contract() -> None:
    service = GatewayService(datalake_client=_FakeDatalakeClient(), market_live_client=_FakeMarketLiveClient())  # type: ignore[arg-type]

    response = await service.backfill_history(
        BackfillRequest(
            symbol="AAPL",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 2),
            chunk_days=365,
        )
    )

    assert response.symbol == "AAPL"
    assert response.rows_written == 2


@pytest.mark.asyncio
async def test_get_current_maps_contract() -> None:
    service = GatewayService(datalake_client=_FakeDatalakeClient(), market_live_client=_FakeMarketLiveClient())  # type: ignore[arg-type]
    response = await service.get_current(symbol="aapl")
    assert response.symbol == "AAPL"
    assert response.trading_date == date(2024, 1, 3)


@pytest.mark.asyncio
async def test_get_current_maps_not_found_error() -> None:
    market_live_client = _FakeMarketLiveClient()
    market_live_client.raise_on_current = UpstreamHttpError(status_code=404, detail="no current bar found")
    service = GatewayService(datalake_client=_FakeDatalakeClient(), market_live_client=market_live_client)  # type: ignore[arg-type]

    with pytest.raises(GatewayError) as exc_info:
        await service.get_current(symbol="ZZZZ")

    assert exc_info.value.status_code == 404
    assert exc_info.value.code == "ticker_not_found"
