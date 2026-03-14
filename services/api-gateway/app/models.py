from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field


@dataclass(frozen=True)
class RequestContext:
    request_id: str
    tenant_id: str | None
    principal_id: str | None


class TickerCreateRequest(BaseModel):
    symbol: str = Field(min_length=1, max_length=32)
    name: str | None = None
    exchange: str | None = None
    asset_type: str | None = None


class TickerResponse(BaseModel):
    id: int
    symbol: str
    name: str | None
    exchange: str | None
    asset_type: str | None
    active: bool


class BarResponse(BaseModel):
    trading_date: date
    open_raw: Decimal | None = None
    high_raw: Decimal | None = None
    low_raw: Decimal | None = None
    close_raw: Decimal | None = None
    volume_raw: int | None = None
    open_adj: Decimal | None = None
    high_adj: Decimal | None = None
    low_adj: Decimal | None = None
    close_adj: Decimal | None = None
    volume_adj: int | None = None


class HistoryResponse(BaseModel):
    symbol: str
    bars: list[BarResponse]


class CurrentResponse(BaseModel):
    symbol: str
    trading_date: date
    open_raw: Decimal | None = None
    high_raw: Decimal | None = None
    low_raw: Decimal | None = None
    close_raw: Decimal | None = None
    volume_raw: int | None = None
    open_adj: Decimal | None = None
    high_adj: Decimal | None = None
    low_adj: Decimal | None = None
    close_adj: Decimal | None = None
    volume_adj: int | None = None


class BackfillRequest(BaseModel):
    symbol: str = Field(min_length=1, max_length=32)
    start_date: date
    end_date: date
    chunk_days: int = Field(default=365, ge=1, le=3650)


class BackfillResponse(BaseModel):
    symbol: str
    ranges_processed: int
    rows_written: int


class ErrorBody(BaseModel):
    code: str
    message: str
    details: dict[str, Any] | None = None


class ErrorResponse(BaseModel):
    error: ErrorBody
