from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class CanonicalTableSource(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    mode: Literal["canonical_tables"] = "canonical_tables"
    tickers_table: str = "tickers"
    bars_table: str = "daily_bars"
    schema_name: str | None = Field(default=None, alias="schema")
    postgres_dsn: str | None = None


class ParquetExportSource(BaseModel):
    mode: Literal["parquet_exports"] = "parquet_exports"
    tickers_parquet_path: str
    bars_parquet_path: str


class PriceRangeRule(BaseModel):
    min_price: float | None = Field(default=None, ge=0)
    max_price: float | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def _validate_bounds(self) -> "PriceRangeRule":
        if self.min_price is None and self.max_price is None:
            raise ValueError("price_range requires min_price or max_price")
        if self.min_price is not None and self.max_price is not None and self.min_price > self.max_price:
            raise ValueError("price_range min_price must be <= max_price")
        return self


class AverageVolumeRule(BaseModel):
    min_average_volume: float = Field(gt=0)
    window_days: int = Field(default=20, ge=2, le=252)


class MomentumRule(BaseModel):
    window_days: int = Field(default=20, ge=2, le=252)
    min_return: float | None = None
    max_return: float | None = None

    @model_validator(mode="after")
    def _validate_bounds(self) -> "MomentumRule":
        if self.min_return is None and self.max_return is None:
            raise ValueError("momentum requires min_return or max_return")
        if self.min_return is not None and self.max_return is not None and self.min_return > self.max_return:
            raise ValueError("momentum min_return must be <= max_return")
        return self


class DrawdownRule(BaseModel):
    max_drawdown_pct: float = Field(ge=0, le=1)
    window_days: int = Field(default=60, ge=2, le=756)


class MovingAverageRule(BaseModel):
    short_window_days: int = Field(default=20, ge=2, le=252)
    long_window_days: int = Field(default=50, ge=2, le=756)
    relation: Literal["above", "below"] = "above"

    @model_validator(mode="after")
    def _validate_windows(self) -> "MovingAverageRule":
        if self.short_window_days >= self.long_window_days:
            raise ValueError("moving_average short_window_days must be < long_window_days")
        return self


class ScreenRules(BaseModel):
    price_range: PriceRangeRule | None = None
    average_volume: AverageVolumeRule | None = None
    momentum: MomentumRule | None = None
    drawdown: DrawdownRule | None = None
    moving_average: MovingAverageRule | None = None

    @model_validator(mode="after")
    def _at_least_one(self) -> "ScreenRules":
        if not any(
            [
                self.price_range,
                self.average_volume,
                self.momentum,
                self.drawdown,
                self.moving_average,
            ]
        ):
            raise ValueError("at least one screening rule is required")
        return self


class ScreenRequest(BaseModel):
    symbols: list[str] = Field(default_factory=list)
    source: CanonicalTableSource | ParquetExportSource = Field(default_factory=CanonicalTableSource)
    start_date: date
    end_date: date
    rules: ScreenRules
    current_prices: dict[str, float] = Field(default_factory=dict)
    current_api_base_url: str | None = None
    include_failed_symbols: bool = False

    @model_validator(mode="after")
    def _validate_dates(self) -> "ScreenRequest":
        if self.start_date > self.end_date:
            raise ValueError("start_date must be <= end_date")
        return self


class ValidateRequest(BaseModel):
    start_date: date
    end_date: date
    rules: ScreenRules


class ValidationResponse(BaseModel):
    valid: bool
    required_history_days: int
    parsed_rules: ScreenRules
    warnings: list[str] = Field(default_factory=list)


class SymbolEvidence(BaseModel):
    latest_price: float | None = None
    average_volume: float | None = None
    momentum_return: float | None = None
    max_drawdown_pct: float | None = None
    short_moving_average: float | None = None
    long_moving_average: float | None = None
    moving_average_relation: str | None = None
    rule_results: dict[str, bool] = Field(default_factory=dict)


class ScreenedSymbol(BaseModel):
    symbol: str
    passed: bool
    evidence: SymbolEvidence


class ScreenResponse(BaseModel):
    screened_symbols: list[ScreenedSymbol]
    selected_symbols: list[str]
    universe_size: int
    selected_count: int
    required_history_days: int


class PresetDefinition(BaseModel):
    key: str
    name: str
    description: str
    rules: ScreenRules
