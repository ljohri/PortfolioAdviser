from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.duckdb_connect import create_duckdb_connection
from tests.factories import seed_screening_bars


@pytest.mark.e2e
def test_submit_criteria_and_receive_screened_output_with_evidence(api_client: TestClient, tmp_path: Path) -> None:
    db_path = tmp_path / "screener.duckdb"
    connection = create_duckdb_connection(database=str(db_path))
    seed_screening_bars(connection)
    connection.close()

    payload = {
        "symbols": ["aapl", "msft", "tsla"],
        "source": {"mode": "canonical_tables", "tickers_table": "tickers", "bars_table": "daily_bars"},
        "start_date": "2024-01-01",
        "end_date": "2024-01-15",
        "rules": {
            "price_range": {"min_price": 95, "max_price": 130},
            "average_volume": {"min_average_volume": 1_000_000, "window_days": 10},
            "momentum": {"window_days": 10, "min_return": 0.03},
            "drawdown": {"window_days": 10, "max_drawdown_pct": 0.1},
            "moving_average": {"short_window_days": 3, "long_window_days": 8, "relation": "above"},
        },
        "include_failed_symbols": True,
    }
    response = api_client.post("/screen/run", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["universe_size"] == 2
    assert body["selected_symbols"] == ["AAPL"]
    assert body["selected_count"] == 1
    assert len(body["screened_symbols"]) == 2

    aapl = next(item for item in body["screened_symbols"] if item["symbol"] == "AAPL")
    assert aapl["passed"] is True
    evidence = aapl["evidence"]
    assert "latest_price" in evidence
    assert "average_volume" in evidence
    assert "momentum_return" in evidence
    assert "max_drawdown_pct" in evidence
    assert "short_moving_average" in evidence
    assert "long_moving_average" in evidence
    assert "rule_results" in evidence
    assert all(evidence["rule_results"].values())


@pytest.mark.e2e
def test_validate_endpoint_and_presets(api_client: TestClient) -> None:
    validate_response = api_client.post(
        "/screen/validate",
        json={
            "start_date": "2024-01-01",
            "end_date": "2024-01-20",
            "rules": {
                "average_volume": {"min_average_volume": 900_000, "window_days": 20},
                "momentum": {"window_days": 15, "min_return": 0.01},
            },
        },
    )
    assert validate_response.status_code == 200
    assert validate_response.json()["valid"] is True
    assert validate_response.json()["required_history_days"] == 20

    presets_response = api_client.get("/screen/presets")
    assert presets_response.status_code == 200
    presets = presets_response.json()
    assert len(presets) >= 2
    assert {preset["key"] for preset in presets} >= {"liquid_momentum", "steady_uptrend"}
