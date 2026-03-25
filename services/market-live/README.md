# market-live

`market-live` is the live market-data service for current bars/quotes.

Tiingo HTTP calls use the shared package `stocklake-tiingo` (see `packages/stocklake-tiingo`), with a thin `app.services.tiingo_client` re-export.

## Development

Member of the **repo-root uv workspace**. From the repository root:

```bash
uv sync --package stocklake-market-live
uv run --package stocklake-market-live python -m pytest tests -q
```

Isolated venv for notebooks (from repo root): `make venv-service SERVICE=market-live` then `source services/market-live/.venv/bin/activate`.

## Responsibilities

- Fetch current/latest market bars directly from provider APIs
- Normalize live payloads into stable service contracts
- Keep live data concerns separate from canonical historical storage

## Local run

From repository root, install deps then start uvicorn from this service directory (so `app` resolves):

```bash
uv sync --package stocklake-market-live
cd services/market-live
../../.venv/bin/uvicorn app.api.main:app --host 0.0.0.0 --port 8001 --reload
```

Environment variables:

- `TIINGO_API_TOKEN` (required for real provider calls)
- `TIINGO_BASE_URL` (default: `https://api.tiingo.com`)
- `APP_ENV` (default: `dev`)

## Tests

Prefer (from repo root):

```bash
uv run --package stocklake-market-live python -m pytest services/market-live/tests -q
```
