from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from mcp_market_live.config import Settings, get_settings
from mcp_market_live.market_live_client import MarketLiveClient


@dataclass
class MarketLiveTools:
    client: MarketLiveClient

    @classmethod
    def from_defaults(cls) -> "MarketLiveTools":
        settings = get_settings()
        return cls(client=_build_client(settings))

    async def get_current_bar(self, *, symbol: str) -> dict[str, Any]:
        return await self.client.get_current_bar(symbol=symbol)


def _build_client(settings: Settings) -> MarketLiveClient:
    return MarketLiveClient(
        base_url=settings.market_live_base_url,
        timeout_seconds=settings.market_live_timeout_seconds,
    )
