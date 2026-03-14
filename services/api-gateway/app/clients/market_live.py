from __future__ import annotations

from typing import Any

import httpx

from app.errors import GatewayError, UpstreamHttpError


class MarketLiveClient:
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

    async def get_current(self, *, symbol: str) -> dict[str, Any]:
        payload = await self._request("GET", f"/current/{symbol.upper()}")
        if not isinstance(payload, dict):
            raise GatewayError(
                status_code=502,
                code="upstream_payload_invalid",
                message="Live market service returned invalid current payload.",
            )
        return payload

    async def _request(self, method: str, path: str) -> Any:
        try:
            async with httpx.AsyncClient(
                base_url=self._base_url,
                timeout=self._timeout_seconds,
                transport=self._transport,
            ) as client:
                response = await client.request(method, path)
        except httpx.TimeoutException as exc:
            raise GatewayError(
                status_code=504,
                code="upstream_timeout",
                message="Live market service timed out.",
            ) from exc
        except httpx.HTTPError as exc:
            raise GatewayError(
                status_code=503,
                code="upstream_unavailable",
                message="Live market service is unavailable.",
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
