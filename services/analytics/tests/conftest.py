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
from app.main import JOB_STORE, create_app


@pytest.fixture(autouse=True)
def _clear_settings_cache() -> Generator[None, None, None]:
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture(autouse=True)
def _clear_job_store() -> Generator[None, None, None]:
    JOB_STORE._jobs.clear()
    yield
    JOB_STORE._jobs.clear()


@pytest.fixture()
def api_client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Generator[TestClient, None, None]:
    db_path = tmp_path / "analytics.duckdb"
    artifacts_dir = tmp_path / "artifacts"
    monkeypatch.setenv("ANALYTICS_DUCKDB_PATH", str(db_path))
    monkeypatch.setenv("ANALYTICS_ARTIFACTS_DIR", str(artifacts_dir))
    app = create_app()
    with TestClient(app) as client:
        yield client
