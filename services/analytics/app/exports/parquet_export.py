from __future__ import annotations

from pathlib import Path

import duckdb


def export_rows_to_parquet(
    connection: duckdb.DuckDBPyConnection,
    *,
    rows: list[dict[str, float | int | str]],
    output_path: str,
) -> str:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    connection.execute("DROP TABLE IF EXISTS analytics_portfolio_export")
    connection.execute(
        """
        CREATE TABLE analytics_portfolio_export (
            symbol VARCHAR,
            latest_rolling_return DOUBLE,
            latest_rolling_volatility DOUBLE,
            max_drawdown DOUBLE,
            momentum_rank INTEGER,
            risk_adjusted_rank INTEGER,
            composite_score DOUBLE,
            composite_rank INTEGER
        )
        """
    )
    if rows:
        values = [
            (
                row["symbol"],
                row["latest_rolling_return"],
                row["latest_rolling_volatility"],
                row["max_drawdown"],
                int(row["momentum_rank"]),
                int(row["risk_adjusted_rank"]),
                row["composite_score"],
                int(row["composite_rank"]),
            )
            for row in rows
        ]
        connection.executemany(
            """
            INSERT INTO analytics_portfolio_export VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            values,
        )
    connection.execute(
        """
        COPY analytics_portfolio_export TO ? (FORMAT PARQUET, COMPRESSION ZSTD)
        """,
        [str(path)],
    )
    return str(path)
