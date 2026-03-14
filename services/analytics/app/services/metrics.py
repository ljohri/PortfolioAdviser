from __future__ import annotations

import math
import statistics


def rolling_return(prices: list[float], *, window: int) -> list[float]:
    if window < 1:
        raise ValueError("window must be >= 1")
    if len(prices) <= window:
        return []
    return [(prices[index] / prices[index - window]) - 1.0 for index in range(window, len(prices))]


def daily_returns(prices: list[float]) -> list[float]:
    if len(prices) < 2:
        return []
    return [(prices[index] / prices[index - 1]) - 1.0 for index in range(1, len(prices))]


def rolling_volatility(returns: list[float], *, window: int, annualization: int = 252) -> list[float]:
    if window < 2:
        raise ValueError("window must be >= 2")
    if len(returns) < window:
        return []
    values: list[float] = []
    for index in range(window - 1, len(returns)):
        window_values = returns[index - window + 1 : index + 1]
        stdev = statistics.stdev(window_values)
        values.append(stdev * math.sqrt(annualization))
    return values


def drawdown_series(prices: list[float]) -> list[float]:
    if not prices:
        return []
    running_peak = prices[0]
    result: list[float] = []
    for price in prices:
        running_peak = max(running_peak, price)
        result.append((price / running_peak) - 1.0)
    return result


def max_drawdown(prices: list[float]) -> float:
    series = drawdown_series(prices)
    return min(series) if series else 0.0
