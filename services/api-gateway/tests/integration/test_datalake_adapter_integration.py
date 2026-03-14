from __future__ import annotations

from datetime import datetime, timezone

import pytest

from app.clients.datalake import DatalakeClient
from app.models import TickerCreateRequest
from tests.helpers import ensure_datalake_reachable, integration_datalake_url


@pytest.mark.integration
@pytest.mark.asyncio
async def test_adapter_can_create_and_list_ticker_against_datalake() -> None:
    ensure_datalake_reachable()
    client = DatalakeClient(base_url=integration_datalake_url(), timeout_seconds=5.0)
    symbol = f"GW{datetime.now(tz=timezone.utc).strftime('%m%d%H%M%S')}"

    created = await client.create_ticker(request=TickerCreateRequest(symbol=symbol))
    tickers = await client.list_tickers()

    assert created["symbol"] == symbol
    assert any(item["symbol"] == symbol for item in tickers)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_adapter_returns_history_shape_against_datalake() -> None:
    ensure_datalake_reachable()
    client = DatalakeClient(base_url=integration_datalake_url(), timeout_seconds=5.0)
    symbol = f"GW{datetime.now(tz=timezone.utc).strftime('%m%d%H%M%S')}"

    await client.create_ticker(request=TickerCreateRequest(symbol=symbol))
    history = await client.list_history(symbol=symbol, start_date=None, end_date=None, limit=25)

    assert isinstance(history, list)
