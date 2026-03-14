from __future__ import annotations

from datetime import date

import pytest

from app.adapters.current_market import CurrentMarketAdapter
from app.adapters.datalake import DatalakeAdapter
from app.duckdb_connect import create_duckdb_connection
from app.models import ScreenRequest
from app.services.engine import ScreenerEngine
from tests.factories import seed_screening_bars


@pytest.mark.integration
def test_screener_engine_filters_symbols_against_seeded_canonical_data(tmp_path) -> None:
    connection = create_duckdb_connection(database=str(tmp_path / "integration.duckdb"))
    seed_screening_bars(connection)
    engine = ScreenerEngine(
        datalake_adapter=DatalakeAdapter(connection),
        current_market_adapter=CurrentMarketAdapter(timeout_seconds=0.1),
    )

    request = ScreenRequest.model_validate(
        {
            "symbols": ["AAPL", "MSFT", "TSLA"],
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
    )

    result = engine.run(request)
    assert result.universe_size == 2
    assert result.selected_symbols == ["AAPL"]
    assert result.selected_count == 1

    aapl = next(item for item in result.screened_symbols if item.symbol == "AAPL")
    msft = next(item for item in result.screened_symbols if item.symbol == "MSFT")
    assert aapl.passed is True
    assert msft.passed is False
    assert aapl.evidence.latest_price is not None
    assert aapl.evidence.average_volume is not None
    assert aapl.evidence.momentum_return is not None
    assert aapl.evidence.max_drawdown_pct is not None
    assert aapl.evidence.short_moving_average is not None
    assert aapl.evidence.long_moving_average is not None
    assert set(aapl.evidence.rule_results.keys()) == {
        "price_range",
        "average_volume",
        "momentum",
        "drawdown",
        "moving_average",
    }


@pytest.mark.integration
def test_validate_criteria_reports_required_history_window(tmp_path) -> None:
    connection = create_duckdb_connection(database=str(tmp_path / "validate.duckdb"))
    engine = ScreenerEngine(
        datalake_adapter=DatalakeAdapter(connection),
        current_market_adapter=CurrentMarketAdapter(timeout_seconds=0.1),
    )
    request = ScreenRequest.model_validate(
        {
            "start_date": date(2024, 1, 1),
            "end_date": date(2024, 1, 20),
            "rules": {
                "average_volume": {"min_average_volume": 500_000, "window_days": 15},
                "momentum": {"window_days": 20, "min_return": 0.01},
                "moving_average": {"short_window_days": 10, "long_window_days": 30, "relation": "above"},
            },
            "source": {"mode": "canonical_tables"},
            "symbols": [],
        }
    )

    response = engine.validate_criteria(request)
    assert response.valid is True
    assert response.required_history_days == 30
    assert response.warnings
