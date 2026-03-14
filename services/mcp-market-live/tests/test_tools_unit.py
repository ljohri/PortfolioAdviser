from __future__ import annotations

import pytest

from mcp_market_live.tools import MarketLiveTools


class _FakeMarketLiveClient:
    async def get_current_bar(self, *, symbol: str):
        return {
            "symbol": symbol.upper(),
            "trading_date": "2024-01-03",
            "close_raw": "150.0",
        }


@pytest.mark.asyncio
async def test_get_current_bar_returns_payload() -> None:
    tools = MarketLiveTools(client=_FakeMarketLiveClient())  # type: ignore[arg-type]
    payload = await tools.get_current_bar(symbol="aapl")
    assert payload["symbol"] == "AAPL"
