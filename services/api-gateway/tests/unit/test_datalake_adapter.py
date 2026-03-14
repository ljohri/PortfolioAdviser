from __future__ import annotations

import httpx
import pytest

from app.clients.datalake import DatalakeClient
from app.errors import GatewayError, UpstreamHttpError
from app.models import TickerCreateRequest


@pytest.mark.asyncio
async def test_list_tickers_maps_success_payload() -> None:
    transport = httpx.MockTransport(
        lambda request: httpx.Response(
            status_code=200,
            json=[{"id": 1, "symbol": "AAPL", "name": None, "exchange": None, "asset_type": None, "active": True}],
        ),
    )
    client = DatalakeClient(base_url="http://datalake.test", timeout_seconds=1.0, transport=transport)

    payload = await client.list_tickers()

    assert payload[0]["symbol"] == "AAPL"


@pytest.mark.asyncio
async def test_create_ticker_rejects_invalid_payload_shape() -> None:
    transport = httpx.MockTransport(lambda request: httpx.Response(status_code=200, json=["not-a-dict"]))
    client = DatalakeClient(base_url="http://datalake.test", timeout_seconds=1.0, transport=transport)

    with pytest.raises(GatewayError) as exc_info:
        await client.create_ticker(TickerCreateRequest(symbol="AAPL"))

    assert exc_info.value.code == "upstream_payload_invalid"


@pytest.mark.asyncio
async def test_http_error_raises_upstream_http_error() -> None:
    transport = httpx.MockTransport(lambda request: httpx.Response(status_code=404, json={"detail": "ticker not found"}))
    client = DatalakeClient(base_url="http://datalake.test", timeout_seconds=1.0, transport=transport)

    with pytest.raises(UpstreamHttpError) as exc_info:
        await client.list_history(symbol="MISSING", start_date=None, end_date=None, limit=10)

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "ticker not found"


@pytest.mark.asyncio
async def test_timeout_maps_to_gateway_timeout_error() -> None:
    def _timeout_handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("timed out", request=request)

    transport = httpx.MockTransport(_timeout_handler)
    client = DatalakeClient(base_url="http://datalake.test", timeout_seconds=0.001, transport=transport)

    with pytest.raises(GatewayError) as exc_info:
        await client.list_tickers()

    assert exc_info.value.status_code == 504
    assert exc_info.value.code == "upstream_timeout"


@pytest.mark.asyncio
async def test_connect_error_maps_to_gateway_unavailable() -> None:
    def _connect_error_handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("cannot connect", request=request)

    transport = httpx.MockTransport(_connect_error_handler)
    client = DatalakeClient(base_url="http://datalake.test", timeout_seconds=1.0, transport=transport)

    with pytest.raises(GatewayError) as exc_info:
        await client.list_tickers()

    assert exc_info.value.status_code == 503
    assert exc_info.value.code == "upstream_unavailable"
