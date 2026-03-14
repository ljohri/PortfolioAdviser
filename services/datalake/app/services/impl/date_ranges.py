from __future__ import annotations

from datetime import date, timedelta


def normalize_backfill_range(start_date: date, end_date: date) -> tuple[date, date]:
    if start_date > end_date:
        raise ValueError("start_date cannot be greater than end_date")
    return start_date, end_date


def split_date_range(start_date: date, end_date: date, chunk_days: int = 365) -> list[tuple[date, date]]:
    start_date, end_date = normalize_backfill_range(start_date, end_date)
    if chunk_days < 1:
        raise ValueError("chunk_days must be >= 1")

    ranges: list[tuple[date, date]] = []
    current = start_date
    while current <= end_date:
        chunk_end = min(current + timedelta(days=chunk_days - 1), end_date)
        ranges.append((current, chunk_end))
        current = chunk_end + timedelta(days=1)
    return ranges
