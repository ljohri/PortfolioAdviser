from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any

import duckdb


@dataclass(frozen=True)
class DatalakeBar:
    symbol: str
    trading_date: date
    close_price: float


class DatalakeAdapter:
    """Reads canonical or exported datalake data for analytics workloads."""

    def __init__(self, connection: duckdb.DuckDBPyConnection) -> None:
        self._connection = connection
        self._postgres_alias = "datalake_pg"

    @property
    def connection(self) -> duckdb.DuckDBPyConnection:
        return self._connection

    def _attach_postgres(self, postgres_dsn: str) -> None:
        self._connection.execute("INSTALL postgres")
        self._connection.execute("LOAD postgres")
        self._connection.execute(
            f"ATTACH '{postgres_dsn}' AS {self._postgres_alias} (TYPE POSTGRES, READ_ONLY)"
        )

    @staticmethod
    def _qualified_table_name(table: str, *, schema: str | None, postgres_alias: str | None) -> str:
        if postgres_alias and schema:
            return f"{postgres_alias}.{schema}.{table}"
        if postgres_alias and not schema:
            return f"{postgres_alias}.main.{table}"
        if schema:
            return f"{schema}.{table}"
        return table

    def normalize_symbol_universe(
        self,
        *,
        symbols: list[str],
        source: dict[str, Any],
    ) -> list[str]:
        canonical = sorted({symbol.strip().upper() for symbol in symbols if symbol.strip()})
        if not canonical:
            return self.list_active_symbols(source=source)
        active = set(self.list_active_symbols(source=source))
        return [symbol for symbol in canonical if symbol in active]

    def list_active_symbols(self, *, source: dict[str, Any]) -> list[str]:
        mode = source["mode"]
        if mode == "canonical_tables":
            postgres_dsn = source.get("postgres_dsn")
            if postgres_dsn:
                self._attach_postgres(postgres_dsn)
            table = self._qualified_table_name(
                source.get("tickers_table", "tickers"),
                schema=source.get("schema") or source.get("schema_name"),
                postgres_alias=self._postgres_alias if postgres_dsn else None,
            )
            rows = self._connection.execute(
                f"""
                SELECT UPPER(symbol) AS symbol
                FROM {table}
                WHERE COALESCE(active, TRUE) = TRUE
                ORDER BY symbol
                """
            ).fetchall()
            return [row[0] for row in rows]
        if mode == "parquet_exports":
            rows = self._connection.execute(
                """
                SELECT UPPER(symbol) AS symbol
                FROM read_parquet(?)
                WHERE COALESCE(active, TRUE) = TRUE
                ORDER BY symbol
                """,
                [source["tickers_parquet_path"]],
            ).fetchall()
            return [row[0] for row in rows]
        raise ValueError(f"Unsupported source mode: {mode}")

    def load_bars(
        self,
        *,
        symbols: list[str],
        start_date: date,
        end_date: date,
        source: dict[str, Any],
    ) -> list[DatalakeBar]:
        if not symbols:
            return []

        mode = source["mode"]
        placeholder = ",".join("?" for _ in symbols)
        if mode == "canonical_tables":
            postgres_dsn = source.get("postgres_dsn")
            if postgres_dsn:
                self._attach_postgres(postgres_dsn)
            tickers_table = self._qualified_table_name(
                source.get("tickers_table", "tickers"),
                schema=source.get("schema") or source.get("schema_name"),
                postgres_alias=self._postgres_alias if postgres_dsn else None,
            )
            bars_table = self._qualified_table_name(
                source.get("bars_table", "daily_bars"),
                schema=source.get("schema") or source.get("schema_name"),
                postgres_alias=self._postgres_alias if postgres_dsn else None,
            )
            rows = self._connection.execute(
                f"""
                SELECT
                    UPPER(t.symbol) AS symbol,
                    b.trading_date,
                    COALESCE(b.close_adj, b.close_raw) AS close_price
                FROM {bars_table} AS b
                INNER JOIN {tickers_table} AS t ON b.ticker_id = t.id
                WHERE UPPER(t.symbol) IN ({placeholder})
                  AND b.trading_date BETWEEN ? AND ?
                  AND COALESCE(b.close_adj, b.close_raw) IS NOT NULL
                ORDER BY symbol, b.trading_date
                """,
                [*symbols, start_date, end_date],
            ).fetchall()
        elif mode == "parquet_exports":
            rows = self._connection.execute(
                f"""
                WITH tickers AS (
                    SELECT id, UPPER(symbol) AS symbol
                    FROM read_parquet(?)
                ),
                bars AS (
                    SELECT ticker_id, trading_date, COALESCE(close_adj, close_raw) AS close_price
                    FROM read_parquet(?)
                )
                SELECT t.symbol, b.trading_date, b.close_price
                FROM bars AS b
                INNER JOIN tickers AS t ON b.ticker_id = t.id
                WHERE t.symbol IN ({placeholder})
                  AND b.trading_date BETWEEN ? AND ?
                  AND b.close_price IS NOT NULL
                ORDER BY t.symbol, b.trading_date
                """,
                [source["tickers_parquet_path"], source["bars_parquet_path"], *symbols, start_date, end_date],
            ).fetchall()
        else:
            raise ValueError(f"Unsupported source mode: {mode}")

        return [
            DatalakeBar(
                symbol=row[0],
                trading_date=row[1],
                close_price=float(row[2]),
            )
            for row in rows
        ]
