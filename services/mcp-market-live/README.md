# mcp-market-live

`mcp-market-live` is the FastMCP server for live/current market data access.

Local venv: from repo root, `make venv-service SERVICE=mcp-market-live` then `source services/mcp-market-live/.venv/bin/activate`.

## Implemented tools

- `get_current_bar(symbol)`

## Run locally

From repository root:

```bash
make venv-service SERVICE=mcp-market-live
source services/mcp-market-live/.venv/bin/activate
python -m mcp_market_live
```

Environment variables:

- `MARKET_LIVE_BASE_URL` (default `http://localhost:8001`)
- `MARKET_LIVE_TIMEOUT_SECONDS` (default `10`)

## Tests

```bash
pytest services/mcp-market-live/tests -q
```
