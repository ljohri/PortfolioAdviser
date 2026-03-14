from __future__ import annotations

import json

import httpx
import pytest

from app.adapters.current_market import CurrentMarketAdapter


@pytest.mark.integration
def test_current_market_adapter_reads_prices_from_http_boundary() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/current/AAPL":
            return httpx.Response(200, content=json.dumps({"symbol": "AAPL", "close": 192.5}))
        if request.url.path == "/current/MSFT":
            return httpx.Response(200, content=json.dumps({"symbol": "MSFT", "close": 415.25}))
        return httpx.Response(404, content=json.dumps({"detail": "not found"}))

    transport = httpx.MockTransport(handler)
    adapter = CurrentMarketAdapter(timeout_seconds=0.1, transport=transport)
    prices = adapter.get_current_prices(symbols=["aapl", "MSFT", "unknown"], base_url="http://market-live:8001")
    assert prices == {"AAPL": 192.5, "MSFT": 415.25}


@pytest.mark.integration
def test_current_market_adapter_handles_transport_failure_deterministically() -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("network unavailable")

    adapter = CurrentMarketAdapter(timeout_seconds=0.1, transport=httpx.MockTransport(handler))
    prices = adapter.get_current_prices(symbols=["AAPL"], base_url="http://market-live:8001")
    assert prices == {}
