# market-live

`market-live` is the live market-data service for current bars/quotes.

## Responsibilities

- Fetch current/latest market bars directly from provider APIs
- Normalize live payloads into stable service contracts
- Keep live data concerns separate from canonical historical storage

## Local run

```bash
uvicorn app.api.main:app --host 0.0.0.0 --port 8001 --reload
```

Environment variables:

- `TIINGO_API_TOKEN` (required for real provider calls)
- `TIINGO_BASE_URL` (default: `https://api.tiingo.com`)
- `APP_ENV` (default: `dev`)

## Tests

```bash
pytest tests -q
```
