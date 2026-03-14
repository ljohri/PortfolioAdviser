from __future__ import annotations

from datetime import date
from decimal import Decimal

from pydantic import BaseModel


class CurrentBarResponse(BaseModel):
    symbol: str
    trading_date: date
    open_raw: Decimal | None
    high_raw: Decimal | None
    low_raw: Decimal | None
    close_raw: Decimal | None
    volume_raw: int | None
    open_adj: Decimal | None
    high_adj: Decimal | None
    low_adj: Decimal | None
    close_adj: Decimal | None
    volume_adj: int | None
