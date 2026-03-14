from __future__ import annotations

import os
from datetime import date, datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from tests.helpers import ensure_datalake_reachable, ensure_market_live_reachable


def _unique_symbol() -> str:
    return f"GW{datetime.now(tz=timezone.utc).strftime('%m%d%H%M%S')}"


@pytest.mark.e2e
def test_add_ticker_then_fetch_history(gateway_client: TestClient) -> None:
    ensure_datalake_reachable()
    symbol = _unique_symbol()

    create_response = gateway_client.post("/v1/tickers", json={"symbol": symbol})
    assert create_response.status_code == 200
    assert create_response.json()["symbol"] == symbol

    history_response = gateway_client.get(f"/v1/history/{symbol}")
    assert history_response.status_code == 200
    body = history_response.json()
    assert body["symbol"] == symbol
    assert isinstance(body["bars"], list)


@pytest.mark.e2e
def test_fetch_missing_ticker_returns_normalized_not_found(gateway_client: TestClient) -> None:
    ensure_datalake_reachable()
    symbol = f"MISSING{datetime.now(tz=timezone.utc).strftime('%H%M%S')}"

    response = gateway_client.get(f"/v1/history/{symbol}")

    assert response.status_code == 404
    payload = response.json()
    assert payload["error"]["code"] == "ticker_not_found"


@pytest.mark.e2e
def test_backfill_flow(gateway_client: TestClient) -> None:
    ensure_datalake_reachable()
    if not os.getenv("TIINGO_API_TOKEN"):
        pytest.skip("TIINGO_API_TOKEN is required for live backfill e2e flow.")

    symbol = _unique_symbol()
    create_response = gateway_client.post("/v1/tickers", json={"symbol": symbol})
    assert create_response.status_code == 200

    end_date = date.today() - timedelta(days=3)
    start_date = end_date - timedelta(days=5)
    backfill_response = gateway_client.post(
        "/v1/history/backfill",
        json={
            "symbol": symbol,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "chunk_days": 365,
        },
    )
    assert backfill_response.status_code == 200
    body = backfill_response.json()
    assert body["symbol"] == symbol
    assert body["ranges_processed"] >= 1
    assert body["rows_written"] >= 0


@pytest.mark.e2e
def test_get_current_flow(gateway_client: TestClient) -> None:
    ensure_market_live_reachable()
    if not os.getenv("TIINGO_API_TOKEN"):
        pytest.skip("TIINGO_API_TOKEN is required for live current e2e flow.")

    response = gateway_client.get("/v1/current/AAPL")
    assert response.status_code == 200
    body = response.json()
    assert body["symbol"] == "AAPL"
    assert "trading_date" in body
