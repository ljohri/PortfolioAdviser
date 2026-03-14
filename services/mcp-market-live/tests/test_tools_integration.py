from __future__ import annotations

import os

import pytest

from mcp_market_live.market_live_client import MarketLiveClient
from mcp_market_live.tools import MarketLiveTools
from tests.conftest import ensure_market_live_reachable, integration_market_live_url


@pytest.mark.integration
@pytest.mark.asyncio
async def test_tools_calls_live_service() -> None:
    ensure_market_live_reachable()
    if not os.getenv("TIINGO_API_TOKEN"):
        pytest.skip("TIINGO_API_TOKEN is required for live integration.")

    tools = MarketLiveTools(
        client=MarketLiveClient(
            base_url=integration_market_live_url(),
            timeout_seconds=10.0,
        )
    )
    payload = await tools.get_current_bar(symbol="AAPL")
    assert payload["symbol"] == "AAPL"
