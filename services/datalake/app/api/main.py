from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.responses import ORJSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.db.engine import get_db_session
from app.repositories.bars import BarRepository
from app.repositories.tickers import TickerRepository
from app.services.backfill_service import BackfillService
from app.services.bar_ingestion_service import BarIngestionService
from app.services.impl.backfill_logic import BackfillServiceImpl
from app.services.impl.bar_ingestion_logic import BarIngestionServiceImpl
from app.services.impl.ticker_logic import TickerServiceImpl
from app.services.ticker_service import TickerService
from app.services.tiingo_client import TiingoClient


class TickerCreateRequest(BaseModel):
    symbol: str = Field(min_length=1, max_length=32)
    name: str | None = None
    exchange: str | None = None
    asset_type: str | None = None


class TickerResponse(BaseModel):
    id: int
    symbol: str
    name: str | None
    exchange: str | None
    asset_type: str | None
    active: bool


class BarResponse(BaseModel):
    symbol: str
    trading_date: date
    open_raw: Decimal | None
    high_raw: Decimal | None
    low_raw: Decimal | None
    close_raw: Decimal | None
    volume_raw: int | None
    open_adj: Decimal | None
    high_adj: Decimal | None
    low_adj: Decimal | None
    close_adj: Decimal | None
    volume_adj: int | None


class BackfillRequest(BaseModel):
    symbol: str = Field(min_length=1, max_length=32)
    start_date: date
    end_date: date
    chunk_days: int = Field(default=365, ge=1, le=3650)


@dataclass
class ServiceContainer:
    ticker_service: TickerService
    backfill_service: BackfillService
    bar_repository: BarRepository


def _build_services(session: Session, settings: Settings) -> ServiceContainer:
    ticker_repository = TickerRepository(session)
    bar_repository = BarRepository(session)
    tiingo_client = TiingoClient(settings)
    ticker_service = TickerService(TickerServiceImpl(ticker_repository=ticker_repository))
    bar_ingestion_service = BarIngestionService(
        BarIngestionServiceImpl(bar_repository=bar_repository),
    )
    backfill_service = BackfillService(
        BackfillServiceImpl(
            session=session,
            ticker_repository=ticker_repository,
            tiingo_client=tiingo_client,
            bar_ingestion_service=bar_ingestion_service,
        ),
    )
    return ServiceContainer(
        ticker_service=ticker_service,
        backfill_service=backfill_service,
        bar_repository=bar_repository,
    )


def create_app() -> FastAPI:
    app = FastAPI(
        title="stocklake-datalake",
        default_response_class=ORJSONResponse,
    )

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/tickers", response_model=TickerResponse)
    def add_ticker(
        payload: TickerCreateRequest,
        session: Session = Depends(get_db_session),
        settings: Settings = Depends(get_settings),
    ) -> TickerResponse:
        services = _build_services(session, settings)
        ticker = services.ticker_service.add_ticker(
            symbol=payload.symbol,
            name=payload.name,
            exchange=payload.exchange,
            asset_type=payload.asset_type,
        )
        session.commit()
        return TickerResponse.model_validate(ticker, from_attributes=True)

    @app.get("/tickers", response_model=list[TickerResponse])
    def list_tickers(
        session: Session = Depends(get_db_session),
        settings: Settings = Depends(get_settings),
    ) -> list[TickerResponse]:
        services = _build_services(session, settings)
        tickers = services.ticker_service.list_tickers()
        return [TickerResponse.model_validate(item, from_attributes=True) for item in tickers]

    @app.get("/bars/{symbol}", response_model=list[BarResponse])
    def get_bars(
        symbol: str,
        start_date: date | None = Query(default=None),
        end_date: date | None = Query(default=None),
        limit: int = Query(default=500, ge=1, le=5000),
        session: Session = Depends(get_db_session),
        settings: Settings = Depends(get_settings),
    ) -> list[BarResponse]:
        services = _build_services(session, settings)
        bars = services.bar_repository.list_by_symbol(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
        )
        response: list[BarResponse] = []
        for bar in bars:
            response.append(
                BarResponse(
                    symbol=symbol.upper(),
                    trading_date=bar.trading_date,
                    open_raw=bar.open_raw,
                    high_raw=bar.high_raw,
                    low_raw=bar.low_raw,
                    close_raw=bar.close_raw,
                    volume_raw=bar.volume_raw,
                    open_adj=bar.open_adj,
                    high_adj=bar.high_adj,
                    low_adj=bar.low_adj,
                    close_adj=bar.close_adj,
                    volume_adj=bar.volume_adj,
                )
            )
        return response

    @app.post("/bars/backfill")
    async def backfill_bars(
        payload: BackfillRequest,
        session: Session = Depends(get_db_session),
        settings: Settings = Depends(get_settings),
    ) -> dict[str, Any]:
        services = _build_services(session, settings)
        try:
            result = await services.backfill_service.backfill(
                symbol=payload.symbol,
                start_date=payload.start_date,
                end_date=payload.end_date,
                chunk_days=payload.chunk_days,
            )
            session.commit()
            return result
        except ValueError as exc:
            session.rollback()
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except Exception as exc:
            session.rollback()
            raise HTTPException(status_code=500, detail="backfill failed") from exc

    return app


app = create_app()
