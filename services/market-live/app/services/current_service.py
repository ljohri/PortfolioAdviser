from __future__ import annotations

from app.models import CurrentBarResponse
from app.services.mapping import map_tiingo_payload_to_current_bar
from app.services.tiingo_client import TiingoClient


class CurrentService:
    def __init__(self, tiingo_client: TiingoClient) -> None:
        self._tiingo_client = tiingo_client

    async def get_current_bar(self, symbol: str) -> CurrentBarResponse | None:
        payload = await self._tiingo_client.get_latest_eod_bar(symbol)
        if payload is None:
            return None
        return map_tiingo_payload_to_current_bar(symbol=symbol, payload_item=payload)
