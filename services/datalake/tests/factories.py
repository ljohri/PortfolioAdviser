from __future__ import annotations

from datetime import date


def ticker_payload(symbol: str = "AAPL") -> dict[str, str]:
    return {
        "symbol": symbol,
        "name": f"{symbol} Inc.",
        "exchange": "NASDAQ",
        "asset_type": "stock",
    }


def tiingo_bar_payload(
    *,
    trading_date: date,
    open_raw: float = 100.0,
    high_raw: float = 110.0,
    low_raw: float = 95.0,
    close_raw: float = 105.0,
    volume_raw: int = 1_000_000,
    adj_open: float = 99.0,
    adj_high: float = 109.0,
    adj_low: float = 94.0,
    adj_close: float = 104.0,
    adj_volume: int = 1_100_000,
) -> dict:
    return {
        "date": f"{trading_date.isoformat()}T00:00:00.000Z",
        "open": open_raw,
        "high": high_raw,
        "low": low_raw,
        "close": close_raw,
        "volume": volume_raw,
        "adjOpen": adj_open,
        "adjHigh": adj_high,
        "adjLow": adj_low,
        "adjClose": adj_close,
        "adjVolume": adj_volume,
        "adjFactor": 1.0,
        "divCash": 0.0,
        "splitFactor": 1.0,
    }
