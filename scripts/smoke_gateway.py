#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import date, timedelta


@dataclass
class CheckResult:
    name: str
    ok: bool
    status: int
    detail: str


def _request(base_url: str, method: str, path: str, payload: dict | None = None) -> tuple[int, dict | list | str | None]:
    data = None
    headers = {"Content-Type": "application/json"}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(f"{base_url}{path}", data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=25) as response:
            body = response.read().decode("utf-8")
            return response.status, json.loads(body) if body else None
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8")
        try:
            return exc.code, json.loads(body) if body else None
        except Exception:
            return exc.code, body


def _short(payload: object) -> str:
    text = json.dumps(payload, sort_keys=True) if not isinstance(payload, str) else payload
    return text[:180]


def run_smoke(base_url: str, strict_live: bool) -> int:
    end_date = date.today() - timedelta(days=3)
    start_date = end_date - timedelta(days=7)
    symbol = f"SMK{int(time.time()) % 1_000_000}"
    missing = f"MISS{int(time.time()) % 1_000_000}"

    checks: list[CheckResult] = []

    status, payload = _request(base_url, "GET", "/health")
    checks.append(CheckResult("health", status == 200, status, _short(payload)))

    status, payload = _request(base_url, "GET", "/v1/tickers")
    checks.append(CheckResult("list_tickers", status == 200, status, _short(payload)))

    status, payload = _request(base_url, "POST", "/v1/tickers", {"symbol": "AAPL"})
    checks.append(CheckResult("ensure_aapl", status == 200, status, _short(payload)))

    status, payload = _request(base_url, "POST", "/v1/tickers", {"symbol": symbol})
    checks.append(CheckResult("add_ticker", status == 200, status, _short(payload)))

    status, payload = _request(base_url, "GET", f"/v1/history/{symbol}")
    checks.append(CheckResult("history_new_symbol", status == 200, status, _short(payload)))

    status, payload = _request(base_url, "GET", f"/v1/history/{missing}")
    missing_ok = status == 404 and isinstance(payload, dict) and payload.get("error", {}).get("code") == "ticker_not_found"
    checks.append(CheckResult("history_missing_symbol", missing_ok, status, _short(payload)))

    backfill_payload = {
        "symbol": "AAPL",
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "chunk_days": 365,
    }
    status, payload = _request(base_url, "POST", "/v1/history/backfill", backfill_payload)
    backfill_ok = status == 200 if strict_live else status in (200, 502)
    checks.append(CheckResult("backfill", backfill_ok, status, _short(payload)))

    status, payload = _request(base_url, "GET", "/v1/current/AAPL")
    current_ok = status == 200 if strict_live else status in (200, 502)
    checks.append(CheckResult("current_aapl", current_ok, status, _short(payload)))

    print(f"Gateway smoke against {base_url}")
    print("-" * 72)
    for item in checks:
        marker = "PASS" if item.ok else "FAIL"
        print(f"{marker:4}  {item.name:22} status={item.status:<3}  {item.detail}")

    failed = [item for item in checks if not item.ok]
    if failed:
        print("-" * 72)
        print(f"Failed checks: {len(failed)}")
        return 1
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke test API gateway endpoints.")
    parser.add_argument("--base-url", default="http://localhost:8080")
    parser.add_argument("--strict-live", action="store_true")
    args = parser.parse_args()
    return run_smoke(base_url=args.base_url, strict_live=args.strict_live)


if __name__ == "__main__":
    raise SystemExit(main())
