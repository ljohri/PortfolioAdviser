from __future__ import annotations

import os
import sys
from pathlib import Path

import httpx
import pytest

SERVICE_ROOT = Path(__file__).resolve().parents[1]
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))


def integration_market_live_url() -> str:
    return os.getenv("INTEGRATION_MARKET_LIVE_BASE_URL", "http://localhost:8001")


def ensure_market_live_reachable() -> None:
    try:
        response = httpx.get(f"{integration_market_live_url().rstrip('/')}/health", timeout=2.0)
        response.raise_for_status()
    except httpx.HTTPError as exc:
        pytest.skip(f"Market-live service is not reachable for integration/e2e tests: {exc}")
