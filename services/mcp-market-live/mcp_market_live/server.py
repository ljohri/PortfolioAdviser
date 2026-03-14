from __future__ import annotations

from fastmcp import FastMCP

from mcp_market_live.tools import MarketLiveTools


def create_server(tools: MarketLiveTools | None = None) -> FastMCP:
    tool_handlers = tools or MarketLiveTools.from_defaults()
    server = FastMCP(name="market-live")

    @server.tool()
    async def get_current_bar(symbol: str) -> dict:
        """
        Fetch the latest available daily bar for one symbol from live provider flows.

        Args:
            symbol: Ticker symbol, such as `AAPL`.

        Returns:
            Current normalized bar payload.
        """
        return await tool_handlers.get_current_bar(symbol=symbol)

    return server


server = create_server()
