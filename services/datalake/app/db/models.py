from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import Date, DateTime, ForeignKey, Index, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    pass


class Ticker(Base):
    __tablename__ = "tickers"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String(32), nullable=False, unique=True)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    exchange: Mapped[str | None] = mapped_column(String(64), nullable=True)
    asset_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    active: Mapped[bool] = mapped_column(default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    bars: Mapped[list["DailyBar"]] = relationship(back_populates="ticker")


class DailyBar(Base):
    __tablename__ = "daily_bars"
    __table_args__ = (
        UniqueConstraint("ticker_id", "trading_date", name="uq_daily_bars_ticker_date"),
        Index("ix_daily_bars_ticker_date", "ticker_id", "trading_date"),
        Index("ix_daily_bars_trading_date", "trading_date"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    ticker_id: Mapped[int] = mapped_column(ForeignKey("tickers.id", ondelete="CASCADE"), nullable=False)
    trading_date: Mapped[date] = mapped_column(Date, nullable=False)

    open_raw: Mapped[Decimal | None] = mapped_column(Numeric(18, 6), nullable=True)
    high_raw: Mapped[Decimal | None] = mapped_column(Numeric(18, 6), nullable=True)
    low_raw: Mapped[Decimal | None] = mapped_column(Numeric(18, 6), nullable=True)
    close_raw: Mapped[Decimal | None] = mapped_column(Numeric(18, 6), nullable=True)
    volume_raw: Mapped[int | None] = mapped_column(nullable=True)

    open_adj: Mapped[Decimal | None] = mapped_column(Numeric(18, 6), nullable=True)
    high_adj: Mapped[Decimal | None] = mapped_column(Numeric(18, 6), nullable=True)
    low_adj: Mapped[Decimal | None] = mapped_column(Numeric(18, 6), nullable=True)
    close_adj: Mapped[Decimal | None] = mapped_column(Numeric(18, 6), nullable=True)
    volume_adj: Mapped[int | None] = mapped_column(nullable=True)
    adj_factor: Mapped[Decimal | None] = mapped_column(Numeric(18, 8), nullable=True)
    dividend_cash: Mapped[Decimal | None] = mapped_column(Numeric(18, 6), nullable=True)
    split_factor: Mapped[Decimal | None] = mapped_column(Numeric(18, 6), nullable=True)

    provider_payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    ingested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    ticker: Mapped[Ticker] = relationship(back_populates="bars")


class TickerSyncState(Base):
    __tablename__ = "ticker_sync_state"
    __table_args__ = (UniqueConstraint("ticker_id", name="uq_ticker_sync_state_ticker_id"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    ticker_id: Mapped[int] = mapped_column(ForeignKey("tickers.id", ondelete="CASCADE"), nullable=False)
    last_successful_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    last_attempted_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="idle")
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class IngestionRun(Base):
    __tablename__ = "ingestion_runs"
    __table_args__ = (Index("ix_ingestion_runs_ticker_id_started_at", "ticker_id", "started_at"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    ticker_id: Mapped[int | None] = mapped_column(ForeignKey("tickers.id", ondelete="SET NULL"), nullable=True)
    source: Mapped[str] = mapped_column(String(64), nullable=False, default="tiingo")
    run_kind: Mapped[str] = mapped_column(String(32), nullable=False, default="backfill")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="started")
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    rows_written: Mapped[int] = mapped_column(nullable=False, default=0)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
