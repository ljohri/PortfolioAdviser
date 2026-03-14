# mcp-market-live

`mcp-market-live` is the FastMCP server for live/current market data access.

## Implemented tools

- `get_current_bar(symbol)`

## Run locally

From repository root:

```bash
python -m pip install -e services/mcp-market-live
python -m mcp_market_live
```

Environment variables:

- `MARKET_LIVE_BASE_URL` (default `http://localhost:8001`)
- `MARKET_LIVE_TIMEOUT_SECONDS` (default `10`)

## Tests

```bash
pytest services/mcp-market-live/tests -q
```
