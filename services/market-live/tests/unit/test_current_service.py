from __future__ import annotations

from datetime import date

import pytest

from app.services.current_service import CurrentService
from tests.factories import tiingo_bar_payload


class _FakeTiingoClient:
    def __init__(self, payload: dict | None) -> None:
        self._payload = payload

    async def get_latest_eod_bar(self, symbol: str):
        return self._payload


@pytest.mark.asyncio
async def test_get_current_bar_returns_none_when_provider_empty() -> None:
    service = CurrentService(tiingo_client=_FakeTiingoClient(payload=None))  # type: ignore[arg-type]
    result = await service.get_current_bar("AAPL")
    assert result is None


@pytest.mark.asyncio
async def test_get_current_bar_maps_payload() -> None:
    service = CurrentService(
        tiingo_client=_FakeTiingoClient(payload=tiingo_bar_payload(trading_date=date(2024, 1, 4))),  # type: ignore[arg-type]
    )
    result = await service.get_current_bar("AAPL")
    assert result is not None
    assert result.symbol == "AAPL"
    assert result.trading_date == date(2024, 1, 4)
