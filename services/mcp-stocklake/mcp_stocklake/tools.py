from __future__ import annotations

from collections.abc import Awaitable, Callable
from contextlib import suppress
from datetime import date
from typing import Any, Protocol

from mcp_stocklake.datalake_service import (
    ServiceDependencies,
    StocklakeRuntime,
    create_stocklake_runtime,
    default_dependencies,
)


class StocklakeServiceLike(Protocol):
    """Protocol for stocklake service methods used by tool wrappers."""

    def add_ticker(self, *, symbol: str, exchange: str | None = None) -> dict[str, Any]:
        raise NotImplementedError

    def list_tickers(self) -> list[dict[str, Any]]:
        raise NotImplementedError

    def get_history(self, *, symbol: str, start: date, end: date) -> list[dict[str, Any]]:
        raise NotImplementedError

    async def backfill_ticker(
        self,
        *,
        symbol: str,
        start: date | None = None,
        end: date | None = None,
    ) -> dict[str, Any]:
        raise NotImplementedError

    def list_missing_ranges(self, *, symbol: str) -> list[dict[str, str]]:
        raise NotImplementedError

    async def run_daily_update(self) -> dict[str, Any]:
        raise NotImplementedError


RuntimeFactory = Callable[[], StocklakeRuntime]


class StocklakeTools:
    """MCP tool wrapper layer responsible for parsing and session control."""

    def __init__(self, runtime_factory: RuntimeFactory) -> None:
        self._runtime_factory = runtime_factory

    @classmethod
    def from_defaults(cls) -> "StocklakeTools":
        """
        Build wrappers using datalake's default runtime dependencies.

        Returns:
            A tool wrapper instance ready for production use.
        """
        deps = default_dependencies()
        return cls(runtime_factory=lambda: create_stocklake_runtime(deps))

    @classmethod
    def from_dependencies(cls, deps: ServiceDependencies) -> "StocklakeTools":
        """
        Build wrappers using explicit dependencies (primarily tests).

        Args:
            deps: Explicit settings/session dependencies.

        Returns:
            A tool wrapper instance bound to provided dependencies.
        """
        return cls(runtime_factory=lambda: create_stocklake_runtime(deps))

    def add_ticker(self, symbol: str, exchange: str | None = None) -> dict[str, Any]:
        """
        Add a ticker symbol to the datalake if it does not already exist.

        Args:
            symbol: The ticker symbol (for example `AAPL`).
            exchange: Optional exchange code (for example `NASDAQ`).

        Returns:
            The canonical ticker record stored in datalake.
        """
        return self._run_sync(lambda service: service.add_ticker(symbol=symbol, exchange=exchange))

    def list_tickers(self) -> list[dict[str, Any]]:
        """
        List all known tickers ordered by symbol.

        Returns:
            A list of ticker records with metadata.
        """
        return self._run_sync(lambda service: service.list_tickers())

    def get_history(self, symbol: str, start: str, end: str) -> list[dict[str, Any]]:
        """
        Retrieve stored daily bar history for a ticker and date window.

        Args:
            symbol: The ticker symbol to query.
            start: Inclusive start date (`YYYY-MM-DD`).
            end: Inclusive end date (`YYYY-MM-DD`).

        Returns:
            Daily OHLCV bars from canonical datalake storage.
        """
        start_date = _parse_date(start)
        end_date = _parse_date(end)
        if start_date > end_date:
            raise ValueError("start date must be on or before end date")
        return self._run_sync(lambda service: service.get_history(symbol=symbol, start=start_date, end=end_date))

    async def backfill_ticker(
        self,
        symbol: str,
        start: str | None = None,
        end: str | None = None,
    ) -> dict[str, Any]:
        """
        Backfill missing daily bars for one ticker via datalake backfill logic.

        Args:
            symbol: Ticker symbol to backfill.
            start: Optional start date (`YYYY-MM-DD`).
            end: Optional end date (`YYYY-MM-DD`).

        Returns:
            Backfill summary including rows written and processed ranges.
        """
        start_date = _parse_date(start) if start else None
        end_date = _parse_date(end) if end else None
        if start_date and end_date and start_date > end_date:
            raise ValueError("start date must be on or before end date")

        return await self._run_async(
            lambda service: service.backfill_ticker(symbol=symbol, start=start_date, end=end_date)
        )

    def list_missing_ranges(self, symbol: str) -> list[dict[str, str]]:
        """
        List missing weekday date ranges for a ticker in canonical storage.

        Args:
            symbol: Ticker symbol to inspect.

        Returns:
            Contiguous missing date ranges with inclusive boundaries.
        """
        return self._run_sync(lambda service: service.list_missing_ranges(symbol=symbol))

    async def run_daily_update(self) -> dict[str, Any]:
        """
        Execute a daily update pass across active tickers.

        Returns:
            Update summary containing per-ticker backfill outcomes.
        """
        return await self._run_async(lambda service: service.run_daily_update())

    def _run_sync(self, operation: Callable[[StocklakeServiceLike], Any]) -> Any:
        runtime = self._runtime_factory()
        try:
            result = operation(runtime.service)
            runtime.session.commit()
            return result
        except Exception:
            runtime.session.rollback()
            raise
        finally:
            with suppress(Exception):
                runtime.session.close()

    async def _run_async(self, operation: Callable[[StocklakeServiceLike], Awaitable[Any]]) -> Any:
        runtime = self._runtime_factory()
        try:
            result = await operation(runtime.service)
            runtime.session.commit()
            return result
        except Exception:
            runtime.session.rollback()
            raise
        finally:
            with suppress(Exception):
                runtime.session.close()


def _parse_date(value: str) -> date:
    return date.fromisoformat(value)

