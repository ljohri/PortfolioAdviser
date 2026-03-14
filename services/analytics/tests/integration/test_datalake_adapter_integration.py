from __future__ import annotations

from datetime import date

import pytest

from app.adapters.datalake import DatalakeAdapter
from app.duckdb_connect import create_duckdb_connection
from tests.factories import seed_realistic_bars


@pytest.mark.integration
def test_adapter_reads_canonical_tables(tmp_path) -> None:
    connection = create_duckdb_connection(database=str(tmp_path / "adapter.duckdb"))
    seed_realistic_bars(connection)
    adapter = DatalakeAdapter(connection)

    source = {
        "mode": "canonical_tables",
        "tickers_table": "tickers",
        "bars_table": "daily_bars",
        "schema": None,
        "postgres_dsn": None,
    }
    normalized = adapter.normalize_symbol_universe(symbols=[" aapl ", "msft", "tsla", "unknown"], source=source)
    assert normalized == ["AAPL", "MSFT"]

    bars = adapter.load_bars(
        symbols=normalized,
        start_date=date(2024, 1, 2),
        end_date=date(2024, 1, 12),
        source=source,
    )
    assert len(bars) == 22
    assert bars[0].symbol == "AAPL"
    assert bars[-1].symbol == "MSFT"


@pytest.mark.integration
def test_adapter_reads_parquet_exports(tmp_path) -> None:
    connection = create_duckdb_connection(database=str(tmp_path / "parquet.duckdb"))
    seed_realistic_bars(connection)
    tickers_path = tmp_path / "tickers.parquet"
    bars_path = tmp_path / "daily_bars.parquet"
    connection.execute("COPY tickers TO ? (FORMAT PARQUET)", [str(tickers_path)])
    connection.execute("COPY daily_bars TO ? (FORMAT PARQUET)", [str(bars_path)])

    adapter = DatalakeAdapter(connection)
    source = {
        "mode": "parquet_exports",
        "tickers_parquet_path": str(tickers_path),
        "bars_parquet_path": str(bars_path),
    }
    normalized = adapter.normalize_symbol_universe(symbols=[], source=source)
    assert normalized == ["AAPL", "MSFT"]

    bars = adapter.load_bars(
        symbols=normalized,
        start_date=date(2024, 1, 2),
        end_date=date(2024, 1, 12),
        source=source,
    )
    assert len(bars) == 22
