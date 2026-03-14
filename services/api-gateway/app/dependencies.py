from __future__ import annotations

from uuid import uuid4

from fastapi import Depends, Header

from app.clients.datalake import DatalakeClient
from app.clients.market_live import MarketLiveClient
from app.config import Settings, get_settings
from app.models import RequestContext
from app.service import GatewayService


def get_request_context(
    x_request_id: str | None = Header(default=None),
    x_tenant_id: str | None = Header(default=None),
) -> RequestContext:
    # Auth is intentionally absent in this phase; context keeps seams stable.
    return RequestContext(
        request_id=x_request_id or str(uuid4()),
        tenant_id=x_tenant_id,
        principal_id=None,
    )


def get_gateway_service(settings: Settings = Depends(get_settings)) -> GatewayService:
    datalake_client = DatalakeClient(
        base_url=settings.datalake_base_url,
        timeout_seconds=settings.datalake_timeout_seconds,
    )
    market_live_client = MarketLiveClient(
        base_url=settings.market_live_base_url,
        timeout_seconds=settings.market_live_timeout_seconds,
    )
    return GatewayService(
        datalake_client=datalake_client,
        market_live_client=market_live_client,
    )
