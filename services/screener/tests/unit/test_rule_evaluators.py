from __future__ import annotations

import math

from app.services.rules import (
    evaluate_average_volume,
    evaluate_drawdown,
    evaluate_momentum,
    evaluate_moving_average_relationship,
    evaluate_price_range,
)


def test_price_range_rule_accepts_value_in_bounds() -> None:
    assert evaluate_price_range(price=50.0, min_price=10.0, max_price=80.0) is True
    assert evaluate_price_range(price=5.0, min_price=10.0, max_price=80.0) is False


def test_average_volume_rule_computes_expected_average() -> None:
    passed, avg = evaluate_average_volume(volumes=[1_000_000, 1_200_000, 800_000], min_average_volume=900_000)
    assert passed is True
    assert avg == 1_000_000


def test_momentum_rule_computes_period_return() -> None:
    passed, momentum = evaluate_momentum(prices=[100, 105, 110], min_return=0.05, max_return=None)
    assert passed is True
    assert math.isclose(momentum, 0.1, rel_tol=1e-9)


def test_drawdown_rule_uses_peak_to_trough() -> None:
    passed, drawdown = evaluate_drawdown(prices=[100, 120, 90, 95], max_drawdown_pct=0.3)
    assert passed is True
    assert math.isclose(drawdown, 0.25, rel_tol=1e-9)


def test_moving_average_relationship_rule() -> None:
    passed, short_ma, long_ma = evaluate_moving_average_relationship(
        prices=[10, 11, 12, 13, 14, 15],
        short_window_days=2,
        long_window_days=5,
        relation="above",
    )
    assert passed is True
    assert short_ma > long_ma
