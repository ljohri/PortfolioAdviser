from __future__ import annotations

from typing import Any

from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.sql.dml import Insert

from app.db.models import DailyBar


UPSERT_COLUMNS = (
    "open_raw",
    "high_raw",
    "low_raw",
    "close_raw",
    "volume_raw",
    "open_adj",
    "high_adj",
    "low_adj",
    "close_adj",
    "volume_adj",
    "adj_factor",
    "dividend_cash",
    "split_factor",
    "provider_payload",
    "updated_at",
)


def build_postgres_upsert_statement(values: list[dict[str, Any]]) -> Insert:
    insert_stmt = pg_insert(DailyBar).values(values)
    update_map = {column: getattr(insert_stmt.excluded, column) for column in UPSERT_COLUMNS}
    return insert_stmt.on_conflict_do_update(
        index_elements=[DailyBar.ticker_id, DailyBar.trading_date],
        set_=update_map,
    )
