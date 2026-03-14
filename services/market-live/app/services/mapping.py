from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

from app.models import CurrentBarResponse


def map_tiingo_payload_to_current_bar(*, symbol: str, payload_item: dict[str, Any]) -> CurrentBarResponse:
    date_value = _parse_date(payload_item.get("date"))
    return CurrentBarResponse(
        symbol=symbol.upper(),
        trading_date=date_value,
        open_raw=_as_decimal(payload_item.get("open")),
        high_raw=_as_decimal(payload_item.get("high")),
        low_raw=_as_decimal(payload_item.get("low")),
        close_raw=_as_decimal(payload_item.get("close")),
        volume_raw=_as_int(payload_item.get("volume")),
        open_adj=_as_decimal(payload_item.get("adjOpen")),
        high_adj=_as_decimal(payload_item.get("adjHigh")),
        low_adj=_as_decimal(payload_item.get("adjLow")),
        close_adj=_as_decimal(payload_item.get("adjClose")),
        volume_adj=_as_int(payload_item.get("adjVolume")),
    )


def _parse_date(value: Any):
    if not isinstance(value, str):
        raise ValueError("payload missing valid date")
    return datetime.fromisoformat(value.replace("Z", "+00:00")).date()


def _as_decimal(value: Any) -> Decimal | None:
    if value is None:
        return None
    return Decimal(str(value))


def _as_int(value: Any) -> int | None:
    if value is None:
        return None
    return int(value)
