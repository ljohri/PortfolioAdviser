from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone

from app.db.models import IngestionRun
from app.repositories.tickers import TickerRepository
from app.services.impl.date_ranges import split_date_range
from app.services.tiingo_client import TiingoClient
from sqlalchemy.orm import Session


@dataclass
class BackfillServiceImpl:
    session: Session
    ticker_repository: TickerRepository
    tiingo_client: TiingoClient
    bar_ingestion_service: "BarIngestionServiceLike"

    async def backfill(self, *, symbol: str, start_date: date, end_date: date, chunk_days: int = 365) -> dict:
        ticker = self.ticker_repository.get_by_symbol(symbol)
        if ticker is None:
            raise ValueError(f"ticker not found: {symbol}")

        ranges = split_date_range(start_date, end_date, chunk_days=chunk_days)
        rows_written = 0
        runs = 0

        for range_start, range_end in ranges:
            run = IngestionRun(
                ticker_id=ticker.id,
                source="tiingo",
                run_kind="backfill",
                status="started",
            )
            self.session.add(run)
            self.session.flush()

            try:
                payload = await self.tiingo_client.get_eod_bars(
                    ticker.symbol,
                    start_date=range_start,
                    end_date=range_end,
                )
                count = self.bar_ingestion_service.ingest_tiingo_payload(
                    ticker_id=ticker.id,
                    payload=payload,
                )
                rows_written += count
                run.rows_written = count
                run.status = "success"
                run.finished_at = datetime.now(tz=timezone.utc)
                self.ticker_repository.upsert_sync_state(
                    ticker_id=ticker.id,
                    status="success",
                    last_attempted_date=range_end,
                    last_successful_date=range_end,
                )
            except Exception as exc:
                run.status = "failed"
                run.error_message = str(exc)
                run.finished_at = datetime.now(tz=timezone.utc)
                self.ticker_repository.upsert_sync_state(
                    ticker_id=ticker.id,
                    status="failed",
                    last_attempted_date=range_end,
                    message=str(exc),
                )
                raise
            finally:
                runs += 1

        return {
            "symbol": ticker.symbol,
            "ranges_processed": runs,
            "rows_written": rows_written,
        }


class BarIngestionServiceLike:
    def ingest_tiingo_payload(self, *, ticker_id: int, payload: list[dict]) -> int:  # pragma: no cover - protocol shim
        raise NotImplementedError
