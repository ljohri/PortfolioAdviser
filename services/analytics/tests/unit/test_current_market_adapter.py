from __future__ import annotations

import httpx
import pytest

from app.adapters.current_market import CurrentMarketAdapter


def test_get_current_prices_parses_market_live_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/current/AAPL":
            return httpx.Response(200, json={"symbol": "AAPL", "close": 189.25})
        if request.url.path == "/current/MSFT":
            return httpx.Response(200, json={"symbol": "MSFT", "price": 410.1})
        return httpx.Response(404, json={"detail": "not found"})

    transport = httpx.MockTransport(handler)
    adapter = CurrentMarketAdapter(timeout_seconds=1.0)

    # Inject transport by monkeypatching Client constructor in a narrow scope.
    class _MockClient(httpx.Client):
        def __init__(self, *args, **kwargs):
            kwargs["transport"] = transport
            super().__init__(*args, **kwargs)

    monkeypatch.setattr(httpx, "Client", _MockClient)
    prices = adapter.get_current_prices(
        symbols=["AAPL", "MSFT", "TSLA"],
        base_url="http://market-live.test",
    )

    assert prices == {"AAPL": 189.25, "MSFT": 410.1}
