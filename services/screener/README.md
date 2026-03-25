# screener

`screener` is a dedicated Python service for rule-based stock screening over canonical market history.

Local venv (Jupyter / IDE): from repo root, `make venv-service SERVICE=screener` then `source services/screener/.venv/bin/activate`.

## Scope

- Evaluate screening criteria against canonical market data (`datalake` contracts only)
- Return filtered candidate symbols with evidence fields
- Remain independent from portfolio-construction and optimization logic
- Support optional current-price enrichment while keeping canonical history as the base input

## Endpoints

- `POST /screen/run`
  - Executes screening rules and returns selected symbols plus per-symbol evidence.
- `POST /screen/validate`
  - Validates criteria and reports required history window.
- `GET /screen/presets`
  - Returns reusable preset rule bundles.

## Implemented rules

- Price range
- Average volume threshold
- Momentum window
- Drawdown filter
- Moving-average relationship

## MCP-ready functions

Internal functions are exposed in `app/mcp_tools.py`:

- `validate_screen(payload)`
- `run_screen(payload)`
- `list_presets()`

These return JSON-serializable shapes for future OpenClaw MCP exposure.

## Test coverage

- Unit: rule evaluators
- Integration: engine + canonical seeded history
- E2E: API workflow from criteria submission to evidence validation
