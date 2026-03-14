---
name: stocklake
description: Use stocklake tools to retrieve and repair canonical EOD market history.
---

# Stocklake

Use stocklake tools whenever the user asks for:
- historical or daily stock prices and related metadata
- backfills or missing market history for historical APIs
- verifying whether local market history exists
- repairing or refreshing ticker history

Rules:
- Prefer canonical stocklake tools over guessing or web-searching price history.
- If history may be missing, call `list_missing_ranges` or `backfill_ticker`.
- For current quotes, use `market-live` MCP tools (for example `get_current_bar`), not historical backfill flows.
- Do not fabricate prices, volumes, splits, or dividends.
- For date-bounded historical requests, call `get_history`.
- For new symbols in historical flows, call `add_ticker` first when needed.
