from __future__ import annotations

import sys
from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

SERVICE_ROOT = Path(__file__).resolve().parents[1]
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))

from app.config import get_settings
from app.main import create_app
from tests.helpers import integration_datalake_url, integration_market_live_url


@pytest.fixture(autouse=True)
def _clear_settings_cache() -> Generator[None, None, None]:
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture()
def gateway_client(monkeypatch: pytest.MonkeyPatch) -> Generator[TestClient, None, None]:
    monkeypatch.setenv("DATALAKE_BASE_URL", integration_datalake_url())
    monkeypatch.setenv("MARKET_LIVE_BASE_URL", integration_market_live_url())
    app = create_app()
    with TestClient(app) as client:
        yield client
