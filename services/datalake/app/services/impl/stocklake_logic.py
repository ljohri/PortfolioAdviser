from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any

from app.db.models import Ticker
from app.repositories.bars import BarRepository
from app.repositories.tickers import TickerRepository
from app.services.backfill_service import BackfillService
from app.services.ticker_service import TickerService


@dataclass(frozen=True)
class MissingRange:
    start: date
    end: date


@dataclass
class StocklakeServiceImpl:
    ticker_service: TickerService
    ticker_repository: TickerRepository
    bar_repository: BarRepository
    backfill_service: BackfillService
    default_backfill_days: int = 30

    def add_ticker(self, *, symbol: str, exchange: str | None = None) -> dict[str, Any]:
        ticker = self.ticker_service.add_ticker(
            symbol=symbol,
            exchange=exchange,
            asset_type="stock",
        )
        return self._serialize_ticker(ticker)

    def list_tickers(self) -> list[dict[str, Any]]:
        return [self._serialize_ticker(item) for item in self.ticker_service.list_tickers()]

    def get_history(self, *, symbol: str, start: date, end: date) -> list[dict[str, Any]]:
        bars = self.bar_repository.list_by_symbol(
            symbol=symbol,
            start_date=start,
            end_date=end,
            limit=10_000,
        )
        return [
            {
                "symbol": symbol.upper(),
                "trading_date": bar.trading_date.isoformat(),
                "open_raw": self._maybe_float(bar.open_raw),
                "high_raw": self._maybe_float(bar.high_raw),
                "low_raw": self._maybe_float(bar.low_raw),
                "close_raw": self._maybe_float(bar.close_raw),
                "volume_raw": bar.volume_raw,
                "open_adj": self._maybe_float(bar.open_adj),
                "high_adj": self._maybe_float(bar.high_adj),
                "low_adj": self._maybe_float(bar.low_adj),
                "close_adj": self._maybe_float(bar.close_adj),
                "volume_adj": bar.volume_adj,
            }
            for bar in bars
        ]

    async def backfill_ticker(
        self,
        *,
        symbol: str,
        start: date | None = None,
        end: date | None = None,
    ) -> dict[str, Any]:
        ticker = self.ticker_repository.get_by_symbol(symbol)
        if ticker is None:
            raise ValueError(f"ticker not found: {symbol}")

        resolved_start, resolved_end = self._resolve_backfill_window(ticker=ticker, start=start, end=end)
        if resolved_start > resolved_end:
            return {
                "symbol": ticker.symbol,
                "start": resolved_start.isoformat(),
                "end": resolved_end.isoformat(),
                "rows_written": 0,
                "ranges_processed": 0,
            }

        result = await self.backfill_service.backfill(
            symbol=ticker.symbol,
            start_date=resolved_start,
            end_date=resolved_end,
            chunk_days=365,
        )
        result["start"] = resolved_start.isoformat()
        result["end"] = resolved_end.isoformat()
        return result

    def list_missing_ranges(self, *, symbol: str) -> list[dict[str, str]]:
        ticker = self.ticker_repository.get_by_symbol(symbol)
        if ticker is None:
            raise ValueError(f"ticker not found: {symbol}")

        today = date.today()
        known_dates = set(self.bar_repository.list_trading_dates(symbol=ticker.symbol, end_date=today))
        if not known_dates:
            start = today - timedelta(days=self.default_backfill_days)
            return [{"start": start.isoformat(), "end": today.isoformat()}]

        first = min(known_dates)
        last = max(known_dates)
        ranges = _compress_missing_weekday_ranges(
            expected_dates=_iter_weekdays(first, today),
            present_dates=known_dates,
        )
        if last < today:
            tail_start = last + timedelta(days=1)
            tail_ranges = _compress_missing_weekday_ranges(
                expected_dates=_iter_weekdays(tail_start, today),
                present_dates=known_dates,
            )
            ranges.extend(tail_ranges)

        return [{"start": item.start.isoformat(), "end": item.end.isoformat()} for item in _dedupe_ranges(ranges)]

    async def run_daily_update(self) -> dict[str, Any]:
        tickers = self.ticker_repository.list_active_tickers()
        updated: list[dict[str, Any]] = []
        for ticker in tickers:
            updated.append(await self.backfill_ticker(symbol=ticker.symbol))
        return {
            "tickers_processed": len(tickers),
            "results": updated,
        }

    def _resolve_backfill_window(
        self,
        *,
        ticker: Ticker,
        start: date | None,
        end: date | None,
    ) -> tuple[date, date]:
        resolved_end = end or date.today()
        if start:
            return start, resolved_end

        sync_state = self.ticker_repository.get_sync_state(ticker_id=ticker.id)
        if sync_state and sync_state.last_successful_date:
            return sync_state.last_successful_date + timedelta(days=1), resolved_end

        latest_bar = self.bar_repository.latest_trading_date(ticker.symbol)
        if latest_bar:
            return latest_bar + timedelta(days=1), resolved_end

        return resolved_end - timedelta(days=self.default_backfill_days), resolved_end

    @staticmethod
    def _serialize_ticker(ticker: Ticker) -> dict[str, Any]:
        return {
            "id": ticker.id,
            "symbol": ticker.symbol,
            "name": ticker.name,
            "exchange": ticker.exchange,
            "asset_type": ticker.asset_type,
            "active": ticker.active,
        }

    @staticmethod
    def _maybe_float(value: Any) -> float | None:
        if value is None:
            return None
        return float(value)


def _iter_weekdays(start: date, end: date) -> list[date]:
    if start > end:
        return []
    values: list[date] = []
    current = start
    while current <= end:
        if current.weekday() < 5:
            values.append(current)
        current += timedelta(days=1)
    return values


def _compress_missing_weekday_ranges(
    *,
    expected_dates: list[date],
    present_dates: set[date],
) -> list[MissingRange]:
    missing = [item for item in expected_dates if item not in present_dates]
    if not missing:
        return []

    ranges: list[MissingRange] = []
    range_start = missing[0]
    previous = missing[0]
    for current in missing[1:]:
        if current == previous + timedelta(days=1):
            previous = current
            continue
        ranges.append(MissingRange(start=range_start, end=previous))
        range_start = current
        previous = current
    ranges.append(MissingRange(start=range_start, end=previous))
    return ranges


def _dedupe_ranges(ranges: list[MissingRange]) -> list[MissingRange]:
    seen: set[tuple[date, date]] = set()
    ordered: list[MissingRange] = []
    for item in ranges:
        key = (item.start, item.end)
        if key in seen:
            continue
        seen.add(key)
        ordered.append(item)
    return ordered
