from __future__ import annotations

import os

import httpx
import pytest


def integration_datalake_url() -> str:
    return os.getenv("INTEGRATION_DATALAKE_BASE_URL", "http://localhost:8000")


def integration_market_live_url() -> str:
    return os.getenv("INTEGRATION_MARKET_LIVE_BASE_URL", "http://localhost:8001")


def ensure_datalake_reachable() -> None:
    try:
        response = httpx.get(f"{integration_datalake_url().rstrip('/')}/health", timeout=2.0)
        response.raise_for_status()
    except httpx.HTTPError as exc:
        pytest.skip(f"Datalake container is not reachable for integration/e2e tests: {exc}")


def ensure_market_live_reachable() -> None:
    try:
        response = httpx.get(f"{integration_market_live_url().rstrip('/')}/health", timeout=2.0)
        response.raise_for_status()
    except httpx.HTTPError as exc:
        pytest.skip(f"Market-live container is not reachable for integration/e2e tests: {exc}")
