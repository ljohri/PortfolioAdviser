from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.duckdb_connect import create_duckdb_connection
from tests.factories import seed_realistic_bars


@pytest.mark.e2e
def test_portfolio_workflow_returns_structured_report(api_client: TestClient, tmp_path: Path) -> None:
    db_path = tmp_path / "analytics.duckdb"
    connection = create_duckdb_connection(database=str(db_path))
    seed_realistic_bars(connection)
    connection.close()

    universe_response = api_client.post(
        "/portfolio/universe",
        json={
            "symbols": ["aapl", "MSFT", "tsla", "  aapl  "],
            "source": {
                "mode": "canonical_tables",
                "tickers_table": "tickers",
                "bars_table": "daily_bars",
            },
        },
    )
    assert universe_response.status_code == 200
    job_id = universe_response.json()["job_id"]
    assert universe_response.json()["normalized_symbols"] == ["AAPL", "MSFT"]

    analyze_response = api_client.post(
        "/portfolio/analyze",
        json={
            "job_id": job_id,
            "start_date": "2024-01-02",
            "end_date": "2024-01-12",
            "rolling_window_days": 5,
            "top_n": 2,
            "export_parquet": True,
        },
    )
    assert analyze_response.status_code == 200
    analyze_body = analyze_response.json()
    assert analyze_body["report_ready"] is True
    assert analyze_body["analysis_mode"] == "historical"
    assert analyze_body["source_mode"] == "canonical_tables"
    assert analyze_body["data_sources_used"] == ["historical"]
    assert analyze_body["current_prices_used"] == 0
    assert analyze_body["symbols_analyzed"] == 2
    assert analyze_body["rows_in_portfolio_input"] == 2
    assert analyze_body["parquet_path"] is not None

    report_response = api_client.get(f"/portfolio/report/{job_id}")
    assert report_response.status_code == 200
    report = report_response.json()
    assert report["job_id"] == job_id
    assert report["analysis_mode"] == "historical"
    assert report["source_mode"] == "canonical_tables"
    assert report["data_sources_used"] == ["historical"]
    assert report["current_prices_used"] == 0
    assert report["rolling_window_days"] == 5
    assert report["symbols"] == ["AAPL", "MSFT"]
    assert len(report["ranking"]) == 2
    assert report["ranking"][0]["composite_rank"] == 1
    assert len(report["portfolio_input_rows"]) == 2
    assert Path(report["parquet_path"]).exists()


@pytest.mark.e2e
def test_portfolio_workflow_current_only(api_client: TestClient, tmp_path: Path) -> None:
    db_path = tmp_path / "analytics.duckdb"
    connection = create_duckdb_connection(database=str(db_path))
    connection.execute("DROP TABLE IF EXISTS tickers")
    connection.execute(
        """
        CREATE TABLE tickers (
            id INTEGER,
            symbol VARCHAR,
            name VARCHAR,
            exchange VARCHAR,
            asset_type VARCHAR,
            active BOOLEAN
        )
        """
    )
    connection.executemany(
        "INSERT INTO tickers VALUES (?, ?, ?, ?, ?, ?)",
        [
            (1, "AAPL", "Apple Inc.", "NASDAQ", "stock", True),
            (2, "MSFT", "Microsoft Corp.", "NASDAQ", "stock", True),
        ],
    )
    connection.close()

    universe_response = api_client.post(
        "/portfolio/universe",
        json={
            "symbols": ["aapl", "msft"],
            "source": {"mode": "canonical_tables", "tickers_table": "tickers"},
        },
    )
    assert universe_response.status_code == 200
    job_id = universe_response.json()["job_id"]

    analyze_response = api_client.post(
        "/portfolio/analyze",
        json={
            "job_id": job_id,
            "start_date": "2024-01-02",
            "end_date": "2024-01-12",
            "data_mode": "current",
            "current_prices": {"AAPL": 190.0, "MSFT": 410.0},
            "export_parquet": False,
        },
    )
    assert analyze_response.status_code == 200
    analyze_body = analyze_response.json()
    assert analyze_body["analysis_mode"] == "current"
    assert analyze_body["data_sources_used"] == ["current"]
    assert analyze_body["current_prices_used"] == 2
    assert analyze_body["symbols_analyzed"] == 2

    report_response = api_client.get(f"/portfolio/report/{job_id}")
    assert report_response.status_code == 200
    report = report_response.json()
    assert report["analysis_mode"] == "current"
    assert report["data_sources_used"] == ["current"]
    assert report["current_prices_used"] == 2
    assert report["ranking"][0]["symbol"] == "MSFT"
    assert report["ranking"][0]["latest_rolling_return"] == 0.0


@pytest.mark.e2e
def test_portfolio_workflow_blended(api_client: TestClient, tmp_path: Path) -> None:
    db_path = tmp_path / "analytics.duckdb"
    connection = create_duckdb_connection(database=str(db_path))
    seed_realistic_bars(connection)
    connection.close()

    universe_response = api_client.post(
        "/portfolio/universe",
        json={
            "symbols": ["aapl", "msft"],
            "source": {"mode": "canonical_tables", "tickers_table": "tickers", "bars_table": "daily_bars"},
        },
    )
    assert universe_response.status_code == 200
    job_id = universe_response.json()["job_id"]

    analyze_response = api_client.post(
        "/portfolio/analyze",
        json={
            "job_id": job_id,
            "start_date": "2024-01-02",
            "end_date": "2024-01-12",
            "rolling_window_days": 5,
            "top_n": 2,
            "data_mode": "blended",
            "current_prices": {"AAPL": 118.0, "MSFT": 205.0},
            "export_parquet": False,
        },
    )
    assert analyze_response.status_code == 200
    analyze_body = analyze_response.json()
    assert analyze_body["analysis_mode"] == "blended"
    assert analyze_body["data_sources_used"] == ["historical", "current"]
    assert analyze_body["current_prices_used"] == 2
    assert analyze_body["symbols_analyzed"] == 2

    report_response = api_client.get(f"/portfolio/report/{job_id}")
    assert report_response.status_code == 200
    report = report_response.json()
    assert report["analysis_mode"] == "blended"
    assert report["data_sources_used"] == ["historical", "current"]
    assert report["current_prices_used"] == 2
    assert len(report["ranking"]) == 2
