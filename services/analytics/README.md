# analytics

`analytics` is a standalone Python service for derived portfolio analytics.

## Service boundaries

- consumes canonical market data from the `datalake`
- computes derived analytics in a DuckDB sidecar
- produces export artifacts for portfolio workflows
- does **not** write canonical market truth back into the datalake
- keeps portfolio workflow logic separate from screener logic

## Implemented API

- `POST /portfolio/universe`
  - normalizes and validates a symbol universe against canonical active tickers
  - creates a workflow `job_id`
- `POST /portfolio/analyze`
  - loads historical closes from canonical tables or parquet exports
  - supports `data_mode`: `historical`, `current`, or `blended`
  - accepts `current_prices` inline and can optionally fetch missing quotes from market-live API
  - returns mode metadata (`analysis_mode`, `source_mode`, `data_sources_used`, `current_prices_used`)
  - computes rolling return, volatility, drawdown, and simple ranking metrics
  - emits a portfolio input dataset and optional parquet export
- `GET /portfolio/report/{job_id}`
  - returns structured derived analytics report for the workflow job, including mode/source metadata

## Inputs

- canonical table mode (`tickers`, `daily_bars`) optionally via Postgres attach
- datalake parquet export mode (`tickers.parquet`, `daily_bars.parquet`)

## Testing

- unit tests for metric calculations
- integration tests for datalake adapter against canonical-shaped and parquet inputs
- one e2e test covering seed -> analyze -> structured report flow
