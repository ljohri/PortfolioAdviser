# mcp-stocklake

`mcp-stocklake` is the FastMCP server used by OpenClaw agents to access canonical historical stocklake data without bypassing datalake business logic.

For live/current bars, use `mcp-market-live`.

## Implemented tools

- `add_ticker(symbol, exchange=None)`
- `list_tickers()`
- `get_history(symbol, start, end)`
- `backfill_ticker(symbol, start=None, end=None)`
- `list_missing_ranges(symbol)`
- `run_daily_update()`

## Run locally

From repository root (uv workspace; requires `datalake` synced so datalake `app` imports resolve):

```bash
cp .env.example .env
uv sync --package stocklake-datalake
uv sync --package stocklake-mcp-stocklake
uv run python -m mcp_stocklake
```

Isolated venv (includes editable `datalake` + `stocklake-tiingo`): from repo root run `make venv-service SERVICE=mcp-stocklake` then `source services/mcp-stocklake/.venv/bin/activate`.

Environment variables:

- `DATABASE_URL` (defaults to local docker postgres URL)
- `TIINGO_API_TOKEN` for real backfills
- `DATALAKE_SERVICE_PATH` only if datalake lives outside `services/datalake`

Prefer setting these in root `.env` (copied from `.env.example`) so Docker and local Python runs use the same contract.

## Tests

From repository root:

```bash
uv sync --package stocklake-mcp-stocklake
uv run --package stocklake-mcp-stocklake python -m pytest services/mcp-stocklake/tests -q
```

Use Docker Postgres for integration and E2E cases:

```bash
docker compose -f infra/docker-compose.yml up -d postgres
```
