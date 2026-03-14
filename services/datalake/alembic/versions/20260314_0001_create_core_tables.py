"""create core datalake tables

Revision ID: 20260314_0001
Revises:
Create Date: 2026-03-14
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260314_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "tickers",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("symbol", sa.String(length=32), nullable=False, unique=True),
        sa.Column("name", sa.String(length=255), nullable=True),
        sa.Column("exchange", sa.String(length=64), nullable=True),
        sa.Column("asset_type", sa.String(length=64), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "daily_bars",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("ticker_id", sa.Integer(), sa.ForeignKey("tickers.id", ondelete="CASCADE"), nullable=False),
        sa.Column("trading_date", sa.Date(), nullable=False),
        sa.Column("open_raw", sa.Numeric(18, 6), nullable=True),
        sa.Column("high_raw", sa.Numeric(18, 6), nullable=True),
        sa.Column("low_raw", sa.Numeric(18, 6), nullable=True),
        sa.Column("close_raw", sa.Numeric(18, 6), nullable=True),
        sa.Column("volume_raw", sa.Integer(), nullable=True),
        sa.Column("open_adj", sa.Numeric(18, 6), nullable=True),
        sa.Column("high_adj", sa.Numeric(18, 6), nullable=True),
        sa.Column("low_adj", sa.Numeric(18, 6), nullable=True),
        sa.Column("close_adj", sa.Numeric(18, 6), nullable=True),
        sa.Column("volume_adj", sa.Integer(), nullable=True),
        sa.Column("adj_factor", sa.Numeric(18, 8), nullable=True),
        sa.Column("dividend_cash", sa.Numeric(18, 6), nullable=True),
        sa.Column("split_factor", sa.Numeric(18, 6), nullable=True),
        sa.Column("provider_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("ingested_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("ticker_id", "trading_date", name="uq_daily_bars_ticker_date"),
    )
    op.create_index("ix_daily_bars_ticker_date", "daily_bars", ["ticker_id", "trading_date"])
    op.create_index("ix_daily_bars_trading_date", "daily_bars", ["trading_date"])

    op.create_table(
        "ticker_sync_state",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("ticker_id", sa.Integer(), sa.ForeignKey("tickers.id", ondelete="CASCADE"), nullable=False),
        sa.Column("last_successful_date", sa.Date(), nullable=True),
        sa.Column("last_attempted_date", sa.Date(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="idle"),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("ticker_id", name="uq_ticker_sync_state_ticker_id"),
    )

    op.create_table(
        "ingestion_runs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("ticker_id", sa.Integer(), sa.ForeignKey("tickers.id", ondelete="SET NULL"), nullable=True),
        sa.Column("source", sa.String(length=64), nullable=False, server_default="tiingo"),
        sa.Column("run_kind", sa.String(length=32), nullable=False, server_default="backfill"),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="started"),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rows_written", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_message", sa.Text(), nullable=True),
    )
    op.create_index("ix_ingestion_runs_ticker_id_started_at", "ingestion_runs", ["ticker_id", "started_at"])


def downgrade() -> None:
    op.drop_index("ix_ingestion_runs_ticker_id_started_at", table_name="ingestion_runs", if_exists=True)
    op.drop_table("ingestion_runs")
    op.drop_table("ticker_sync_state")
    op.drop_index("ix_daily_bars_trading_date", table_name="daily_bars", if_exists=True)
    op.drop_index("ix_daily_bars_ticker_date", table_name="daily_bars", if_exists=True)
    op.drop_table("daily_bars")
    op.drop_table("tickers")
