from __future__ import annotations

import httpx
import pytest

from app.clients.market_live import MarketLiveClient
from app.errors import GatewayError, UpstreamHttpError


@pytest.mark.asyncio
async def test_get_current_success_payload() -> None:
    transport = httpx.MockTransport(
        lambda request: httpx.Response(
            status_code=200,
            json={
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
            },
        ),
    )
    client = MarketLiveClient(base_url="http://market-live.test", timeout_seconds=1.0, transport=transport)
    payload = await client.get_current(symbol="AAPL")
    assert payload["symbol"] == "AAPL"


@pytest.mark.asyncio
async def test_get_current_invalid_shape() -> None:
    transport = httpx.MockTransport(lambda request: httpx.Response(status_code=200, json=["bad"]))
    client = MarketLiveClient(base_url="http://market-live.test", timeout_seconds=1.0, transport=transport)
    with pytest.raises(GatewayError) as exc_info:
        await client.get_current(symbol="AAPL")
    assert exc_info.value.code == "upstream_payload_invalid"


@pytest.mark.asyncio
async def test_get_current_404_maps_upstream_http_error() -> None:
    transport = httpx.MockTransport(lambda request: httpx.Response(status_code=404, json={"detail": "not found"}))
    client = MarketLiveClient(base_url="http://market-live.test", timeout_seconds=1.0, transport=transport)
    with pytest.raises(UpstreamHttpError) as exc_info:
        await client.get_current(symbol="MISSING")
    assert exc_info.value.status_code == 404
