from __future__ import annotations

from datetime import date


def tiingo_bar_payload(*, trading_date: date, close_raw: float = 105.0, adj_close: float = 104.0) -> dict:
    return {
        "date": f"{trading_date.isoformat()}T00:00:00.000Z",
        "open": 100.0,
        "high": 110.0,
        "low": 95.0,
        "close": close_raw,
        "volume": 1_000_000,
        "adjOpen": 99.0,
        "adjHigh": 109.0,
        "adjLow": 94.0,
        "adjClose": adj_close,
        "adjVolume": 1_100_000,
        "adjFactor": 1.0,
        "divCash": 0.0,
        "splitFactor": 1.0,
    }
