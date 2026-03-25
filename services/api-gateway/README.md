# api-gateway

`api-gateway` is the SaaS-facing facade for external API consumers.

This service is **not** in the repo-root uv workspace. Use a **local** venv for development or Jupyter:

```bash
# from repository root
make venv-service SERVICE=api-gateway
source services/api-gateway/.venv/bin/activate
```

## Responsibilities

- Provide stable, versioned HTTP endpoints (`/v1/*`)
- Route requests to `datalake` through adapter clients
- Normalize upstream failures into a predictable error contract
- Keep route handlers thin and reserve room for future auth/quota/tenant middleware

## Local run

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
```

Environment variables:

- `DATALAKE_BASE_URL` (default: `http://localhost:8000`)
- `DATALAKE_TIMEOUT_SECONDS` (default: `10`)
- `MARKET_LIVE_BASE_URL` (default: `http://localhost:8001`)
- `MARKET_LIVE_TIMEOUT_SECONDS` (default: `10`)
- `APP_ENV` (default: `dev`)

## Test suites

- `tests/unit`: adapter and mapping behavior
- `tests/integration`: adapter calls against running datalake container
- `tests/e2e`: gateway workflows through HTTP endpoints
