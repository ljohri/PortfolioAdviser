from __future__ import annotations

from datetime import date
from decimal import Decimal

from app.services.impl.tiingo_mapping import map_tiingo_payload_to_upsert
from tests.factories import tiingo_bar_payload


def test_map_tiingo_payload_to_upsert_preserves_raw_and_adjusted_fields() -> None:
    payload = tiingo_bar_payload(trading_date=date(2024, 1, 2), open_raw=101.25, adj_close=103.75)
    row = map_tiingo_payload_to_upsert(ticker_id=7, payload_item=payload)

    assert row.ticker_id == 7
    assert row.trading_date == date(2024, 1, 2)
    assert row.open_raw == Decimal("101.25")
    assert row.close_adj == Decimal("103.75")
    assert row.provider_payload == payload
