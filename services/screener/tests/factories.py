from __future__ import annotations

from datetime import date, timedelta


def seed_screening_bars(connection) -> None:
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
            close_adj DOUBLE,
            volume_raw BIGINT,
            volume_adj BIGINT
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

    start = date(2024, 1, 1)
    aapl_prices = [
        100,
        101,
        102,
        103,
        104,
        105,
        106,
        107,
        108,
        110,
        112,
        113,
        115,
        116,
        118,
    ]
    msft_prices = [
        100,
        99,
        98,
        96,
        94,
        95,
        97,
        96,
        95,
        94,
        93,
        92,
        91,
        90,
        89,
    ]
    aapl_volume = [1_600_000 + i * 10_000 for i in range(len(aapl_prices))]
    msft_volume = [400_000 + i * 5_000 for i in range(len(msft_prices))]

    rows: list[tuple[int, int, date, float, float, int, int]] = []
    row_id = 1
    for idx, price in enumerate(aapl_prices):
        trade_date = start + timedelta(days=idx)
        rows.append((row_id, 1, trade_date, float(price), float(price), aapl_volume[idx], aapl_volume[idx]))
        row_id += 1
    for idx, price in enumerate(msft_prices):
        trade_date = start + timedelta(days=idx)
        rows.append((row_id, 2, trade_date, float(price), float(price), msft_volume[idx], msft_volume[idx]))
        row_id += 1
    connection.executemany("INSERT INTO daily_bars VALUES (?, ?, ?, ?, ?, ?, ?)", rows)
