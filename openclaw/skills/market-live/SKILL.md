---
name: market-live
description: Use market-live tools to retrieve current/latest market bars.
---

# Market Live

Use market-live tools whenever the user asks for:
- current/latest bar data for symbols
- near-real-time market checks that should not depend on historical backfills

Rules:
- Prefer `get_current_bar` for current snapshots.
- Do not call historical repair/backfill tools for current reads.
- If a symbol is missing current data, report the tool error clearly.
- Do not fabricate prices, volumes, splits, or dividends.
