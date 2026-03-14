from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.repositories.bars import BarRepository
from app.services.impl.tiingo_mapping import map_tiingo_payload_to_upsert


@dataclass
class BarIngestionServiceImpl:
    bar_repository: BarRepository

    def ingest_tiingo_payload(self, *, ticker_id: int, payload: list[dict[str, Any]]) -> int:
        rows = [map_tiingo_payload_to_upsert(ticker_id=ticker_id, payload_item=item) for item in payload]
        return self.bar_repository.upsert_daily_bars(rows)
