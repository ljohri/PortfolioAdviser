from __future__ import annotations


def ticker_payload(symbol: str) -> dict[str, str | None]:
    return {
        "symbol": symbol.upper(),
        "name": f"{symbol.upper()} Corp",
        "exchange": "NASDAQ",
        "asset_type": "equity",
    }
