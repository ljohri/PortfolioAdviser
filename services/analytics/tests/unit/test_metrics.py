from __future__ import annotations

import math

from app.services.metrics import daily_returns, drawdown_series, max_drawdown, rolling_return, rolling_volatility


def test_rolling_return_computes_expected_values() -> None:
    prices = [100.0, 105.0, 110.0, 121.0]
    values = rolling_return(prices, window=2)
    assert math.isclose(values[0], 0.1, rel_tol=1e-9)
    assert math.isclose(values[1], 0.15238095238095228, rel_tol=1e-9)


def test_rolling_volatility_annualizes_window_stdev() -> None:
    returns = [0.01, -0.02, 0.015, 0.005]
    values = rolling_volatility(returns, window=3, annualization=252)
    assert len(values) == 2
    assert values[0] > 0
    assert math.isclose(values[0], 0.3004995840263344, rel_tol=1e-9)


def test_drawdown_series_and_max_drawdown() -> None:
    prices = [100.0, 120.0, 90.0, 95.0]
    series = drawdown_series(prices)
    assert series == [0.0, 0.0, -0.25, -0.20833333333333337]
    assert max_drawdown(prices) == -0.25


def test_daily_returns_empty_or_single_price() -> None:
    assert daily_returns([]) == []
    assert daily_returns([100.0]) == []
