from __future__ import annotations

from datetime import date

import pytest

from app.services.impl.date_ranges import normalize_backfill_range, split_date_range


def test_split_date_range_returns_inclusive_chunks() -> None:
    ranges = split_date_range(date(2024, 1, 1), date(2024, 1, 10), chunk_days=4)
    assert ranges == [
        (date(2024, 1, 1), date(2024, 1, 4)),
        (date(2024, 1, 5), date(2024, 1, 8)),
        (date(2024, 1, 9), date(2024, 1, 10)),
    ]


def test_split_date_range_single_day() -> None:
    ranges = split_date_range(date(2024, 2, 1), date(2024, 2, 1), chunk_days=365)
    assert ranges == [(date(2024, 2, 1), date(2024, 2, 1))]


def test_normalize_backfill_range_rejects_invalid_order() -> None:
    with pytest.raises(ValueError):
        normalize_backfill_range(date(2024, 2, 2), date(2024, 2, 1))
