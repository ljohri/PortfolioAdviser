from __future__ import annotations

from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from mcp_stocklake.datalake_runtime import bootstrap_datalake_path
from mcp_stocklake.server import create_server
from mcp_stocklake.tools import StocklakeTools

bootstrap_datalake_path()

from app.api.main import create_app  # noqa: E402
from app.config import get_settings  # noqa: E402
from app.db.engine import get_db_session  # noqa: E402
from app.services.tiingo_client import TiingoClient  # noqa: E402


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_datalake_and_mcp_end_to_end_flow(
    stocklake_tools: StocklakeTools,
    db_session_factory: sessionmaker,
    service_dependencies,
    tiingo_payload_factory,
    monkeypatch,
) -> None:
    datalake_app = create_app()

    def override_get_db_session():
        session = db_session_factory()
        try:
            yield session
            session.commit()
        finally:
            session.close()

    datalake_app.dependency_overrides[get_db_session] = override_get_db_session
    datalake_app.dependency_overrides[get_settings] = lambda: service_dependencies.settings

    mcp_server = create_server(tools=stocklake_tools)
    assert mcp_server is not None

    async def fake_get_eod_bars(self, symbol: str, *, start_date: date, end_date: date):
        return [
            tiingo_payload_factory(trading_date=start_date, close=150.0),
            tiingo_payload_factory(trading_date=end_date, close=151.0),
        ]

    monkeypatch.setattr(TiingoClient, "get_eod_bars", fake_get_eod_bars)

    with TestClient(datalake_app) as datalake_client:
        health = datalake_client.get("/health")
        assert health.status_code == 200

        stocklake_tools.add_ticker("AAPL", exchange="NASDAQ")
        backfill = await stocklake_tools.backfill_ticker("AAPL", start="2024-01-01", end="2024-01-02")
        assert backfill["rows_written"] == 2

        bars_response = datalake_client.get("/bars/AAPL?start_date=2024-01-01&end_date=2024-01-02")
        assert bars_response.status_code == 200
        bars = bars_response.json()
        assert len(bars) == 2
        assert bars[0]["symbol"] == "AAPL"

    datalake_app.dependency_overrides.clear()

