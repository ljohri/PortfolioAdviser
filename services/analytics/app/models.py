from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


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


class UniverseRequest(BaseModel):
    symbols: list[str] = Field(default_factory=list)
    source: CanonicalTableSource | ParquetExportSource = Field(default_factory=CanonicalTableSource)


class UniverseResponse(BaseModel):
    job_id: str
    normalized_symbols: list[str]
    source_mode: str


class AnalyzeRequest(BaseModel):
    job_id: str
    start_date: date
    end_date: date
    rolling_window_days: int = Field(default=20, ge=2, le=252)
    top_n: int = Field(default=10, ge=1, le=200)
    data_mode: Literal["historical", "current", "blended"] = "historical"
    current_prices: dict[str, float] = Field(default_factory=dict)
    current_api_base_url: str | None = None
    export_parquet: bool = True


class MetricRow(BaseModel):
    symbol: str
    latest_rolling_return: float
    latest_rolling_volatility: float
    max_drawdown: float
    momentum_rank: int
    risk_adjusted_rank: int
    composite_score: float
    composite_rank: int


class AnalyzeResponse(BaseModel):
    job_id: str
    report_ready: bool
    analysis_mode: Literal["historical", "current", "blended"]
    source_mode: str
    data_sources_used: list[str]
    current_prices_used: int
    symbols_analyzed: int
    rows_in_portfolio_input: int
    parquet_path: str | None


class PortfolioReport(BaseModel):
    job_id: str
    generated_at: str
    analysis_mode: Literal["historical", "current", "blended"]
    source_mode: str
    data_sources_used: list[str]
    current_prices_used: int
    start_date: date
    end_date: date
    rolling_window_days: int
    symbols: list[str]
    ranking: list[MetricRow]
    portfolio_input_rows: list[dict[str, float | str]]
    parquet_path: str | None
