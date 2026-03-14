from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from app.repositories.bars import DailyBarUpsert


def _to_decimal(value: Any) -> Decimal | None:
    if value is None:
        return None
    return Decimal(str(value))


def _parse_date(value: str | None) -> date:
    if not value:
        raise ValueError("tiingo payload is missing date")
    return datetime.fromisoformat(value.replace("Z", "+00:00")).date()


def map_tiingo_payload_to_upsert(
    *,
    ticker_id: int,
    payload_item: dict[str, Any],
) -> DailyBarUpsert:
    return DailyBarUpsert(
        ticker_id=ticker_id,
        trading_date=_parse_date(payload_item.get("date")),
        open_raw=_to_decimal(payload_item.get("open")),
        high_raw=_to_decimal(payload_item.get("high")),
        low_raw=_to_decimal(payload_item.get("low")),
        close_raw=_to_decimal(payload_item.get("close")),
        volume_raw=payload_item.get("volume"),
        open_adj=_to_decimal(payload_item.get("adjOpen")),
        high_adj=_to_decimal(payload_item.get("adjHigh")),
        low_adj=_to_decimal(payload_item.get("adjLow")),
        close_adj=_to_decimal(payload_item.get("adjClose")),
        volume_adj=payload_item.get("adjVolume"),
        adj_factor=_to_decimal(payload_item.get("adjFactor")),
        dividend_cash=_to_decimal(payload_item.get("divCash")),
        split_factor=_to_decimal(payload_item.get("splitFactor")),
        provider_payload=payload_item,
    )
