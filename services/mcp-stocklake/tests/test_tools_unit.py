from __future__ import annotations

from datetime import date
from typing import Any

import pytest

from mcp_stocklake.datalake_service import StocklakeRuntime
from mcp_stocklake.tools import StocklakeTools


class _FakeSession:
    def __init__(self) -> None:
        self.commits = 0
        self.rollbacks = 0
        self.closed = 0

    def commit(self) -> None:
        self.commits += 1

    def rollback(self) -> None:
        self.rollbacks += 1

    def close(self) -> None:
        self.closed += 1


class _FakeService:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict[str, Any]]] = []

    def add_ticker(self, *, symbol: str, exchange: str | None = None) -> dict[str, Any]:
        self.calls.append(("add_ticker", {"symbol": symbol, "exchange": exchange}))
        return {"symbol": symbol.upper(), "exchange": exchange}

    def list_tickers(self) -> list[dict[str, Any]]:
        self.calls.append(("list_tickers", {}))
        return [{"symbol": "AAPL"}]

    def get_history(self, *, symbol: str, start: date, end: date) -> list[dict[str, Any]]:
        self.calls.append(("get_history", {"symbol": symbol, "start": start, "end": end}))
        return [{"symbol": symbol.upper(), "trading_date": start.isoformat()}]

    async def backfill_ticker(
        self,
        *,
        symbol: str,
        start: date | None = None,
        end: date | None = None,
    ) -> dict[str, Any]:
        self.calls.append(("backfill_ticker", {"symbol": symbol, "start": start, "end": end}))
        return {"symbol": symbol.upper(), "rows_written": 2}

    def list_missing_ranges(self, *, symbol: str) -> list[dict[str, str]]:
        self.calls.append(("list_missing_ranges", {"symbol": symbol}))
        return [{"start": "2024-01-01", "end": "2024-01-05"}]

    async def run_daily_update(self) -> dict[str, Any]:
        self.calls.append(("run_daily_update", {}))
        return {"tickers_processed": 1}


def test_sync_tool_wrapper_commits_and_returns_payload() -> None:
    service = _FakeService()
    session = _FakeSession()
    tools = StocklakeTools(runtime_factory=lambda: StocklakeRuntime(service=service, session=session))  # type: ignore[arg-type]

    result = tools.add_ticker("aapl", exchange="NASDAQ")

    assert result == {"symbol": "AAPL", "exchange": "NASDAQ"}
    assert ("add_ticker", {"symbol": "aapl", "exchange": "NASDAQ"}) in service.calls
    assert session.commits == 1
    assert session.rollbacks == 0
    assert session.closed == 1


@pytest.mark.asyncio
async def test_async_tool_wrapper_parses_dates_and_calls_service() -> None:
    service = _FakeService()
    session = _FakeSession()
    tools = StocklakeTools(runtime_factory=lambda: StocklakeRuntime(service=service, session=session))  # type: ignore[arg-type]

    result = await tools.backfill_ticker("MSFT", start="2024-01-01", end="2024-01-02")

    assert result == {"symbol": "MSFT", "rows_written": 2}
    assert ("backfill_ticker", {"symbol": "MSFT", "start": date(2024, 1, 1), "end": date(2024, 1, 2)}) in service.calls
    assert session.commits == 1
    assert session.rollbacks == 0
    assert session.closed == 1


def test_get_history_rejects_invalid_window() -> None:
    service = _FakeService()
    session = _FakeSession()
    tools = StocklakeTools(runtime_factory=lambda: StocklakeRuntime(service=service, session=session))  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="start date must be on or before end date"):
        tools.get_history("AAPL", "2024-01-10", "2024-01-01")

    assert session.commits == 0
    assert session.rollbacks == 0
    assert session.closed == 0

