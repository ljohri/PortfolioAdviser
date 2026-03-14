from __future__ import annotations

import os

import pytest

from app.clients.market_live import MarketLiveClient
from tests.helpers import ensure_market_live_reachable, integration_market_live_url


@pytest.mark.integration
@pytest.mark.asyncio
async def test_market_live_adapter_get_current_against_service() -> None:
    ensure_market_live_reachable()
    if not os.getenv("TIINGO_API_TOKEN"):
        pytest.skip("TIINGO_API_TOKEN is required for live current integration flow.")

    client = MarketLiveClient(base_url=integration_market_live_url(), timeout_seconds=10.0)
    payload = await client.get_current(symbol="AAPL")
    assert payload["symbol"] == "AAPL"
    assert "trading_date" in payload
