from __future__ import annotations

from datetime import date, timedelta


def seed_canonical_tables(connection) -> None:
    connection.execute("DROP TABLE IF EXISTS tickers")
    connection.execute("DROP TABLE IF EXISTS daily_bars")
    connection.execute(
        """
        CREATE TABLE tickers (
            id INTEGER,
            symbol VARCHAR,
            name VARCHAR,
            exchange VARCHAR,
            asset_type VARCHAR,
            active BOOLEAN
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE daily_bars (
            id INTEGER,
            ticker_id INTEGER,
            trading_date DATE,
            close_raw DOUBLE,
            close_adj DOUBLE
        )
        """
    )
    connection.executemany(
        "INSERT INTO tickers VALUES (?, ?, ?, ?, ?, ?)",
        [
            (1, "AAPL", "Apple Inc.", "NASDAQ", "stock", True),
            (2, "MSFT", "Microsoft Corp.", "NASDAQ", "stock", True),
            (3, "TSLA", "Tesla Inc.", "NASDAQ", "stock", False),
        ],
    )


def _series(start: float, increments: list[float]) -> list[float]:
    values = [start]
    for delta in increments:
        values.append(values[-1] * (1.0 + delta))
    return values


def seed_realistic_bars(connection) -> None:
    seed_canonical_tables(connection)
    start_date = date(2024, 1, 2)
    aapl_prices = _series(100.0, [0.01, 0.008, -0.004, 0.012, 0.01, -0.003, 0.009, 0.007, -0.002, 0.011])
    msft_prices = _series(200.0, [0.006, -0.005, 0.004, 0.003, -0.008, 0.005, 0.004, -0.004, 0.002, 0.003])
    rows: list[tuple[int, int, date, float, float]] = []
    bar_id = 1
    for index, price in enumerate(aapl_prices):
        rows.append((bar_id, 1, start_date + timedelta(days=index), price, price))
        bar_id += 1
    for index, price in enumerate(msft_prices):
        rows.append((bar_id, 2, start_date + timedelta(days=index), price, price))
        bar_id += 1
    connection.executemany("INSERT INTO daily_bars VALUES (?, ?, ?, ?, ?)", rows)
