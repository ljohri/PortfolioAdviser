# OpenClaw Integration: Stocklake + Market-Live MCP

This document describes how to run `mcp-stocklake` and `mcp-market-live`, wire them into OpenClaw, and guide agent behavior with dedicated skills.

## Run the MCP servers

From repository root:

```bash
python -m pip install -e services/datalake -e services/market-live -e services/mcp-stocklake -e services/mcp-market-live
python -m mcp_stocklake
python -m mcp_market_live
```

Recommended environment variables:

- `DATABASE_URL=postgresql+psycopg://stocklake:stocklake@localhost:5432/stocklake`
- `TIINGO_API_TOKEN=<token>` (required for live backfills)
- `DATALAKE_SERVICE_PATH=<optional custom path>`
- `MARKET_LIVE_BASE_URL=http://localhost:8001`

`mcp-stocklake` exposes the following historical/canonical tools:

- `add_ticker`
- `list_tickers`
- `get_history`
- `backfill_ticker`
- `list_missing_ranges`
- `run_daily_update`

`mcp-market-live` exposes:

- `get_current_bar`

## OpenClaw MCP configuration

Add both MCP servers as stdio servers in OpenClaw:

```json
{
  "mcpServers": {
    "stocklake": {
      "command": "python",
      "args": ["-m", "mcp_stocklake"],
      "env": {
        "DATABASE_URL": "postgresql+psycopg://stocklake:stocklake@localhost:5432/stocklake",
        "TIINGO_API_TOKEN": "${TIINGO_API_TOKEN}"
      }
    },
    "market-live": {
      "command": "python",
      "args": ["-m", "mcp_market_live"],
      "env": {
        "MARKET_LIVE_BASE_URL": "http://localhost:8001",
        "MARKET_LIVE_TIMEOUT_SECONDS": "10"
      }
    }
  }
}
```

Use the same `DATABASE_URL` as datalake so historical tools share canonical state.

## Skill guidance for OpenClaw

`openclaw/skills/stocklake/SKILL.md` should keep historical/canonical behavior narrow and safety-focused:

- use stocklake tools for ticker metadata and price history tasks
- prefer `get_history` and `backfill_ticker` to retrieve/fix data
- never fabricate or infer exact prices when data is missing
- keep tool usage deterministic and concise

`openclaw/skills/market-live/SKILL.md` should guide current/live flows through `get_current_bar` and avoid historical backfill tools for current reads.

Skills should stay as behavior guidance only, not business logic.
