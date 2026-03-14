from __future__ import annotations

from datetime import date
from decimal import Decimal

from app.services.mapping import map_tiingo_payload_to_current_bar
from tests.factories import tiingo_bar_payload


def test_map_tiingo_payload_to_current_bar() -> None:
    payload = tiingo_bar_payload(trading_date=date(2024, 1, 3), close_raw=150.0, adj_close=149.25)

    mapped = map_tiingo_payload_to_current_bar(symbol="aapl", payload_item=payload)

    assert mapped.symbol == "AAPL"
    assert mapped.trading_date == date(2024, 1, 3)
    assert mapped.close_raw == Decimal("150.0")
    assert mapped.close_adj == Decimal("149.25")
