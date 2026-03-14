from __future__ import annotations

from datetime import date
from typing import Any

import httpx

from app.errors import GatewayError, UpstreamHttpError
from app.models import BackfillRequest, TickerCreateRequest


class DatalakeClient:
    def __init__(
        self,
        *,
        base_url: str,
        timeout_seconds: float,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout_seconds = timeout_seconds
        self._transport = transport

    async def list_tickers(self) -> list[dict[str, Any]]:
        payload = await self._request("GET", "/tickers")
        if not isinstance(payload, list):
            raise GatewayError(
                status_code=502,
                code="upstream_payload_invalid",
                message="Market data service returned invalid ticker payload.",
            )
        return payload

    async def create_ticker(self, request: TickerCreateRequest) -> dict[str, Any]:
        payload = await self._request("POST", "/tickers", json=request.model_dump(mode="json"))
        if not isinstance(payload, dict):
            raise GatewayError(
                status_code=502,
                code="upstream_payload_invalid",
                message="Market data service returned invalid ticker payload.",
            )
        return payload

    async def list_history(
        self,
        *,
        symbol: str,
        start_date: date | None,
        end_date: date | None,
        limit: int,
    ) -> list[dict[str, Any]]:
        params: dict[str, Any] = {"limit": limit}
        if start_date is not None:
            params["start_date"] = start_date.isoformat()
        if end_date is not None:
            params["end_date"] = end_date.isoformat()
        payload = await self._request("GET", f"/bars/{symbol.upper()}", params=params)
        if not isinstance(payload, list):
            raise GatewayError(
                status_code=502,
                code="upstream_payload_invalid",
                message="Market data service returned invalid history payload.",
            )
        return payload

    async def backfill_history(self, request: BackfillRequest) -> dict[str, Any]:
        payload = await self._request("POST", "/bars/backfill", json=request.model_dump(mode="json"))
        if not isinstance(payload, dict):
            raise GatewayError(
                status_code=502,
                code="upstream_payload_invalid",
                message="Market data service returned invalid backfill payload.",
            )
        return payload

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
    ) -> Any:
        try:
            async with httpx.AsyncClient(
                base_url=self._base_url,
                timeout=self._timeout_seconds,
                transport=self._transport,
            ) as client:
                response = await client.request(method, path, params=params, json=json)
        except httpx.TimeoutException as exc:
            raise GatewayError(
                status_code=504,
                code="upstream_timeout",
                message="Market data service timed out.",
            ) from exc
        except httpx.HTTPError as exc:
            raise GatewayError(
                status_code=503,
                code="upstream_unavailable",
                message="Market data service is unavailable.",
            ) from exc

        if response.status_code >= 400:
            detail = _extract_error_detail(response)
            raise UpstreamHttpError(status_code=response.status_code, detail=detail)

        return response.json()


def _extract_error_detail(response: httpx.Response) -> str | None:
    try:
        payload = response.json()
    except ValueError:
        return response.text or None
    if isinstance(payload, dict):
        detail = payload.get("detail")
        if isinstance(detail, str):
            return detail
    return None
