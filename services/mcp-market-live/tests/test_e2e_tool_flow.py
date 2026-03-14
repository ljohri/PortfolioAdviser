from __future__ import annotations

import os

import pytest

from mcp_market_live.server import create_server
from mcp_market_live.tools import MarketLiveTools
from tests.conftest import ensure_market_live_reachable


class _FakeClient:
    async def get_current_bar(self, *, symbol: str):
        return {"symbol": symbol.upper(), "trading_date": "2024-01-03", "close_raw": "150.0"}


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_server_binds_get_current_tool() -> None:
    server = create_server(tools=MarketLiveTools(client=_FakeClient()))  # type: ignore[arg-type]
    assert server is not None


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_live_tool_end_to_end_path() -> None:
    ensure_market_live_reachable()
    if not os.getenv("TIINGO_API_TOKEN"):
        pytest.skip("TIINGO_API_TOKEN is required for live e2e.")

    from mcp_market_live.market_live_client import MarketLiveClient

    tools = MarketLiveTools(client=MarketLiveClient(base_url="http://localhost:8001", timeout_seconds=10.0))
    payload = await tools.get_current_bar(symbol="AAPL")
    assert payload["symbol"] == "AAPL"
