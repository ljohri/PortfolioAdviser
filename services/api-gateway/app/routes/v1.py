from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, Query

from app.dependencies import get_gateway_service, get_request_context
from app.models import BackfillRequest, BackfillResponse, CurrentResponse, ErrorResponse, HistoryResponse, RequestContext, TickerCreateRequest, TickerResponse
from app.service import GatewayService


router = APIRouter(prefix="/v1", tags=["v1"])


@router.get("/tickers", response_model=list[TickerResponse], responses={502: {"model": ErrorResponse}, 503: {"model": ErrorResponse}, 504: {"model": ErrorResponse}})
async def list_tickers(
    _: RequestContext = Depends(get_request_context),
    gateway_service: GatewayService = Depends(get_gateway_service),
) -> list[TickerResponse]:
    return await gateway_service.list_tickers()


@router.post("/tickers", response_model=TickerResponse, responses={400: {"model": ErrorResponse}, 502: {"model": ErrorResponse}, 503: {"model": ErrorResponse}, 504: {"model": ErrorResponse}})
async def create_ticker(
    payload: TickerCreateRequest,
    _: RequestContext = Depends(get_request_context),
    gateway_service: GatewayService = Depends(get_gateway_service),
) -> TickerResponse:
    return await gateway_service.create_ticker(payload)


@router.get("/history/{symbol}", response_model=HistoryResponse, responses={404: {"model": ErrorResponse}, 502: {"model": ErrorResponse}, 503: {"model": ErrorResponse}, 504: {"model": ErrorResponse}})
async def get_history(
    symbol: str,
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    limit: int = Query(default=500, ge=1, le=5000),
    _: RequestContext = Depends(get_request_context),
    gateway_service: GatewayService = Depends(get_gateway_service),
) -> HistoryResponse:
    return await gateway_service.get_history(
        symbol=symbol,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
    )


@router.get("/current/{symbol}", response_model=CurrentResponse, responses={404: {"model": ErrorResponse}, 502: {"model": ErrorResponse}, 503: {"model": ErrorResponse}, 504: {"model": ErrorResponse}})
async def get_current(
    symbol: str,
    _: RequestContext = Depends(get_request_context),
    gateway_service: GatewayService = Depends(get_gateway_service),
) -> CurrentResponse:
    return await gateway_service.get_current(symbol=symbol)


@router.post("/history/backfill", response_model=BackfillResponse, responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}, 502: {"model": ErrorResponse}, 503: {"model": ErrorResponse}, 504: {"model": ErrorResponse}})
async def backfill_history(
    payload: BackfillRequest,
    _: RequestContext = Depends(get_request_context),
    gateway_service: GatewayService = Depends(get_gateway_service),
) -> BackfillResponse:
    return await gateway_service.backfill_history(payload)
