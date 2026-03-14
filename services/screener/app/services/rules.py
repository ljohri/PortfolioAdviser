from __future__ import annotations

from statistics import mean


def evaluate_price_range(*, price: float, min_price: float | None, max_price: float | None) -> bool:
    if min_price is not None and price < min_price:
        return False
    if max_price is not None and price > max_price:
        return False
    return True


def evaluate_average_volume(*, volumes: list[float], min_average_volume: float) -> tuple[bool, float]:
    average = mean(volumes) if volumes else 0.0
    return average >= min_average_volume, average


def evaluate_momentum(
    *,
    prices: list[float],
    min_return: float | None,
    max_return: float | None,
) -> tuple[bool, float]:
    if len(prices) < 2 or prices[0] <= 0:
        return False, 0.0
    momentum = (prices[-1] / prices[0]) - 1.0
    if min_return is not None and momentum < min_return:
        return False, momentum
    if max_return is not None and momentum > max_return:
        return False, momentum
    return True, momentum


def evaluate_drawdown(*, prices: list[float], max_drawdown_pct: float) -> tuple[bool, float]:
    if not prices:
        return False, 1.0
    peak = prices[0]
    worst = 0.0
    for value in prices:
        if value > peak:
            peak = value
        if peak <= 0:
            continue
        drawdown = (peak - value) / peak
        if drawdown > worst:
            worst = drawdown
    return worst <= max_drawdown_pct, worst


def evaluate_moving_average_relationship(
    *,
    prices: list[float],
    short_window_days: int,
    long_window_days: int,
    relation: str,
) -> tuple[bool, float, float]:
    short_ma = mean(prices[-short_window_days:])
    long_ma = mean(prices[-long_window_days:])
    if relation == "above":
        return short_ma > long_ma, short_ma, long_ma
    return short_ma < long_ma, short_ma, long_ma
