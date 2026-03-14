from __future__ import annotations

from fastapi.testclient import TestClient

from tests.factories import ticker_payload


def test_add_ticker_and_list_tickers(client: TestClient) -> None:
    create_response = client.post("/tickers", json=ticker_payload("AAPL"))
    assert create_response.status_code == 200
    assert create_response.json()["symbol"] == "AAPL"

    list_response = client.get("/tickers")
    assert list_response.status_code == 200
    body = list_response.json()
    assert len(body) == 1
    assert body[0]["symbol"] == "AAPL"
