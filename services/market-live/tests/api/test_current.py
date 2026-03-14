from __future__ import annotations

from datetime import date
from decimal import Decimal

from app.services.tiingo_client import TiingoClient
from tests.factories import tiingo_bar_payload


def test_get_current_endpoint(client, monkeypatch) -> None:
    async def fake_get_latest_eod_bar(self, symbol: str, lookback_days: int = 10):
        assert symbol == "AAPL"
        return tiingo_bar_payload(trading_date=date(2024, 1, 3), close_raw=150.0, adj_close=149.25)

    monkeypatch.setattr(TiingoClient, "get_latest_eod_bar", fake_get_latest_eod_bar)

    response = client.get("/current/AAPL")
    assert response.status_code == 200
    body = response.json()
    assert body["symbol"] == "AAPL"
    assert body["trading_date"] == "2024-01-03"
    assert Decimal(body["close_raw"]) == Decimal("150.0")
    assert Decimal(body["close_adj"]) == Decimal("149.25")


def test_get_current_endpoint_404_when_missing(client, monkeypatch) -> None:
    async def fake_get_latest_eod_bar(self, symbol: str, lookback_days: int = 10):
        return None

    monkeypatch.setattr(TiingoClient, "get_latest_eod_bar", fake_get_latest_eod_bar)

    response = client.get("/current/ZZZZ")
    assert response.status_code == 404
    assert "no current bar found" in response.json()["detail"]
