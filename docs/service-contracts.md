# Service Contracts

This document defines the public SaaS-facing HTTP contract exposed by `services/api-gateway`.

For interactive calls against a running gateway, use the template notebook [`services/api-gateway/notebooks/explore.ipynb`](../services/api-gateway/notebooks/explore.ipynb) (after `make venv-service SERVICE=api-gateway` and starting uvicorn or Compose).

## API gateway principles

- Public API is versioned under `/v1`.
- `api-gateway` translates public calls into `datalake` and `market-live` upstream calls.
- Internal repository and storage details are never exposed in public responses.
- Error payloads are normalized so clients can rely on stable machine-readable codes.
- Auth, quotas, and tenant enforcement are not active yet, but request context seams already exist for future middleware.

## Base endpoints

### `GET /health`

Response:

```json
{
  "status": "ok"
}
```

### `GET /v1/tickers`

Response:

```json
[
  {
    "id": 1,
    "symbol": "AAPL",
    "name": "Apple Inc.",
    "exchange": "NASDAQ",
    "asset_type": "equity",
    "active": true
  }
]
```

### `POST /v1/tickers`

Request:

```json
{
  "symbol": "AAPL",
  "name": "Apple Inc.",
  "exchange": "NASDAQ",
  "asset_type": "equity"
}
```

Response:

```json
{
  "id": 1,
  "symbol": "AAPL",
  "name": "Apple Inc.",
  "exchange": "NASDAQ",
  "asset_type": "equity",
  "active": true
}
```

### `GET /v1/history/{symbol}`

Query params:

- `start_date` (optional, `YYYY-MM-DD`)
- `end_date` (optional, `YYYY-MM-DD`)
- `limit` (optional, default `500`, max `5000`)

Response:

```json
{
  "symbol": "AAPL",
  "bars": [
    {
      "trading_date": "2024-01-02",
      "open_raw": "100.0",
      "high_raw": "110.0",
      "low_raw": "95.0",
      "close_raw": "105.0",
      "volume_raw": 1000000,
      "open_adj": "99.0",
      "high_adj": "109.0",
      "low_adj": "94.0",
      "close_adj": "104.0",
      "volume_adj": 1100000
    }
  ]
}
```

### `GET /v1/current/{symbol}`

Response:

```json
{
  "symbol": "AAPL",
  "trading_date": "2024-01-03",
  "open_raw": "100.0",
  "high_raw": "110.0",
  "low_raw": "95.0",
  "close_raw": "105.0",
  "volume_raw": 1000000,
  "open_adj": "99.0",
  "high_adj": "109.0",
  "low_adj": "94.0",
  "close_adj": "104.0",
  "volume_adj": 1100000
}
```

### `POST /v1/history/backfill`

Request:

```json
{
  "symbol": "AAPL",
  "start_date": "2024-01-01",
  "end_date": "2024-01-15",
  "chunk_days": 365
}
```

Response:

```json
{
  "symbol": "AAPL",
  "ranges_processed": 1,
  "rows_written": 10
}
```

## Normalized error contract

All gateway-generated failures use:

```json
{
  "error": {
    "code": "ticker_not_found",
    "message": "Ticker 'MSFT' was not found.",
    "details": null
  }
}
```

Common error codes:

- `invalid_request` (`400`)
- `ticker_not_found` (`404`)
- `not_found` (`404`)
- `upstream_failure` (`502`)
- `upstream_unavailable` (`503`)
- `upstream_timeout` (`504`)
