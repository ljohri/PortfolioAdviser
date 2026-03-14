from __future__ import annotations

from fastmcp import FastMCP

from mcp_stocklake.tools import StocklakeTools


def create_server(tools: StocklakeTools | None = None) -> FastMCP:
    """
    Create the FastMCP server with stocklake tool bindings.

    Args:
        tools: Optional tool wrapper dependency for testing.

    Returns:
        Configured FastMCP server instance.
    """
    tool_handlers = tools or StocklakeTools.from_defaults()
    server = FastMCP(name="stocklake")

    @server.tool()
    def add_ticker(symbol: str, exchange: str | None = None) -> dict:
        """
        Add a ticker to canonical stocklake storage.

        Args:
            symbol: Ticker symbol, such as `AAPL`.
            exchange: Optional exchange code, such as `NASDAQ`.

        Returns:
            Canonical ticker metadata for the stored symbol.
        """
        return tool_handlers.add_ticker(symbol=symbol, exchange=exchange)

    @server.tool()
    def list_tickers() -> list[dict]:
        """
        List all known ticker symbols in canonical storage.

        Returns:
            Ticker metadata records ordered by symbol.
        """
        return tool_handlers.list_tickers()

    @server.tool()
    def get_history(symbol: str, start: str, end: str) -> list[dict]:
        """
        Fetch stored daily bars for one symbol and date window.

        Args:
            symbol: Ticker symbol to query.
            start: Inclusive start date in `YYYY-MM-DD`.
            end: Inclusive end date in `YYYY-MM-DD`.

        Returns:
            Daily OHLCV bar records from canonical storage.
        """
        return tool_handlers.get_history(symbol=symbol, start=start, end=end)

    @server.tool()
    async def backfill_ticker(
        symbol: str,
        start: str | None = None,
        end: str | None = None,
    ) -> dict:
        """
        Backfill ticker history through datalake ingestion pipelines.

        Args:
            symbol: Ticker symbol to backfill.
            start: Optional start date in `YYYY-MM-DD`.
            end: Optional end date in `YYYY-MM-DD`.

        Returns:
            Backfill summary with written row counts and range stats.
        """
        return await tool_handlers.backfill_ticker(symbol=symbol, start=start, end=end)

    @server.tool()
    def list_missing_ranges(symbol: str) -> list[dict]:
        """
        Compute missing weekday bar ranges for a ticker.

        Args:
            symbol: Ticker symbol to inspect.

        Returns:
            Inclusive date ranges representing missing history segments.
        """
        return tool_handlers.list_missing_ranges(symbol=symbol)

    @server.tool()
    async def run_daily_update() -> dict:
        """
        Run a daily synchronization pass over active tickers.

        Returns:
            Batch summary containing per-ticker backfill outcomes.
        """
        return await tool_handlers.run_daily_update()

    return server


server = create_server()

