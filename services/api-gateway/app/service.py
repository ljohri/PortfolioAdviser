from __future__ import annotations

from datetime import date

from app.clients.datalake import DatalakeClient
from app.clients.market_live import MarketLiveClient
from app.errors import GatewayError, UpstreamHttpError
from app.models import BackfillRequest, BackfillResponse, BarResponse, CurrentResponse, HistoryResponse, TickerCreateRequest, TickerResponse


class GatewayService:
    def __init__(self, *, datalake_client: DatalakeClient, market_live_client: MarketLiveClient) -> None:
        self._datalake_client = datalake_client
        self._market_live_client = market_live_client

    async def list_tickers(self) -> list[TickerResponse]:
        payload = await self._invoke(self._datalake_client.list_tickers)
        return [TickerResponse.model_validate(item) for item in payload]

    async def create_ticker(self, request: TickerCreateRequest) -> TickerResponse:
        payload = await self._invoke(self._datalake_client.create_ticker, request)
        return TickerResponse.model_validate(payload)

    async def get_history(
        self,
        *,
        symbol: str,
        start_date: date | None,
        end_date: date | None,
        limit: int,
    ) -> HistoryResponse:
        normalized_symbol = symbol.upper()
        tickers = await self._invoke(self._datalake_client.list_tickers)
        if not any(item.get("symbol") == normalized_symbol for item in tickers if isinstance(item, dict)):
            raise GatewayError(
                status_code=404,
                code="ticker_not_found",
                message=f"Ticker '{normalized_symbol}' was not found.",
            )

        bars_payload = await self._invoke(
            self._datalake_client.list_history,
            symbol=normalized_symbol,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
        )
        return HistoryResponse(
            symbol=normalized_symbol,
            bars=[BarResponse.model_validate(item) for item in bars_payload],
        )

    async def backfill_history(self, request: BackfillRequest) -> BackfillResponse:
        payload = await self._invoke(
            self._datalake_client.backfill_history,
            request,
            symbol_hint=request.symbol.upper(),
        )
        return BackfillResponse.model_validate(payload)

    async def get_current(self, *, symbol: str) -> CurrentResponse:
        payload = await self._invoke(
            self._market_live_client.get_current,
            symbol=symbol.upper(),
            symbol_hint=symbol.upper(),
        )
        return CurrentResponse.model_validate(payload)

    async def _invoke(self, operation, *args, symbol_hint: str | None = None, **kwargs):
        try:
            return await operation(*args, **kwargs)
        except UpstreamHttpError as exc:
            raise _map_upstream_http_error(exc, symbol_hint=symbol_hint) from exc


def _map_upstream_http_error(exc: UpstreamHttpError, *, symbol_hint: str | None = None) -> GatewayError:
    if exc.status_code == 400:
        return GatewayError(
            status_code=400,
            code="invalid_request",
            message="The request was rejected by the market data service.",
        )

    if exc.status_code == 404:
        if symbol_hint is not None:
            return GatewayError(
                status_code=404,
                code="ticker_not_found",
                message=f"Ticker '{symbol_hint}' was not found.",
            )
        return GatewayError(
            status_code=404,
            code="not_found",
            message="The requested resource was not found.",
        )

    if 500 <= exc.status_code:
        return GatewayError(
            status_code=502,
            code="upstream_failure",
            message="Market data service failed to process the request.",
        )

    return GatewayError(
        status_code=502,
        code="upstream_failure",
        message="Market data service returned an unexpected response.",
    )
