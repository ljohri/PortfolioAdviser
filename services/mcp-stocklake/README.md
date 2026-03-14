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

From repository root:

```bash
cp .env.example .env
python -m pip install -e services/datalake -e services/mcp-stocklake
python -m mcp_stocklake
```

Environment variables:

- `DATABASE_URL` (defaults to local docker postgres URL)
- `TIINGO_API_TOKEN` for real backfills
- `DATALAKE_SERVICE_PATH` only if datalake lives outside `services/datalake`

Prefer setting these in root `.env` (copied from `.env.example`) so Docker and local Python runs use the same contract.

## Tests

```bash
pytest services/mcp-stocklake/tests -q
```

Use Docker Postgres for integration and E2E cases:

```bash
docker compose -f infra/docker-compose.yml up -d postgres
```
