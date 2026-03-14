from __future__ import annotations

from app.services.impl.bar_ingestion_logic import BarIngestionServiceImpl


class BarIngestionService:
    """Thin facade delegating ingestion details to impl module."""

    def __init__(self, impl: BarIngestionServiceImpl) -> None:
        self._impl = impl

    def ingest_tiingo_payload(self, *, ticker_id: int, payload: list[dict]) -> int:
        return self._impl.ingest_tiingo_payload(ticker_id=ticker_id, payload=payload)
