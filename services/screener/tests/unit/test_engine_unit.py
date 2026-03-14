from __future__ import annotations

from datetime import date

from app.models import ScreenRequest
from app.services.engine import ScreenerEngine


class _NoopDatalakeAdapter:
    def normalize_symbol_universe(self, *, symbols, source):  # type: ignore[no-untyped-def]
        return symbols

    def load_bars(self, *, symbols, start_date, end_date, source):  # type: ignore[no-untyped-def]
        return []


class _NoopCurrentAdapter:
    def get_current_prices(self, *, symbols, base_url):  # type: ignore[no-untyped-def]
        return {}


def test_required_history_days_uses_longest_rule_window() -> None:
    engine = ScreenerEngine(
        datalake_adapter=_NoopDatalakeAdapter(),  # type: ignore[arg-type]
        current_market_adapter=_NoopCurrentAdapter(),  # type: ignore[arg-type]
    )
    request = ScreenRequest.model_validate(
        {
            "symbols": ["AAPL"],
            "source": {"mode": "canonical_tables"},
            "start_date": date(2024, 1, 1),
            "end_date": date(2024, 2, 1),
            "rules": {
                "average_volume": {"min_average_volume": 1_000_000, "window_days": 15},
                "momentum": {"window_days": 20, "min_return": 0.02},
                "drawdown": {"window_days": 45, "max_drawdown_pct": 0.2},
                "moving_average": {"short_window_days": 20, "long_window_days": 60, "relation": "above"},
            },
        }
    )
    assert engine.required_history_days(request) == 60


def test_validate_criteria_warns_when_requested_range_is_too_short() -> None:
    engine = ScreenerEngine(
        datalake_adapter=_NoopDatalakeAdapter(),  # type: ignore[arg-type]
        current_market_adapter=_NoopCurrentAdapter(),  # type: ignore[arg-type]
    )
    request = ScreenRequest.model_validate(
        {
            "symbols": ["AAPL"],
            "source": {"mode": "canonical_tables"},
            "start_date": date(2024, 1, 1),
            "end_date": date(2024, 1, 10),
            "rules": {
                "moving_average": {"short_window_days": 20, "long_window_days": 50, "relation": "above"},
            },
        }
    )
    response = engine.validate_criteria(request)
    assert response.valid is True
    assert response.required_history_days == 50
    assert response.warnings
