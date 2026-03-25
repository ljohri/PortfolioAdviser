# Testing Strategy

This strategy sets minimal but clear expectations for service-level testing while the platform is in scaffold and early implementation phases.

## Test level definitions

- Unit tests: validate isolated functions/classes with no network or database dependency.
- Integration tests: validate interactions across components (for example, service + datastore contract) with controlled dependencies.
- End-to-end (E2E) tests: validate user- or agent-facing flows across multiple services from interface to persistence boundary.

## Tooling: uv workspace (selected services)

`datalake`, `market-live`, and `mcp-stocklake` are members of a **repo-root uv workspace** with a shared lockfile (`uv.lock`). They depend on `stocklake-tiingo` as a workspace package.

- Prefer: from repository root, `uv sync --package <project-name>` then `uv run --package <project-name> python -m pytest <path> -q` (use `python -m pytest` so the synced environment is used).
- Project names: `stocklake-datalake`, `stocklake-market-live`, `stocklake-mcp-stocklake`.
- Other services (for example `api-gateway`, `analytics`, `screener`) are not in the workspace yet; install with `pip install ./services/<name>` in a virtual environment and run `pytest` as usual.

CI mirrors this split (see `.github/workflows/ci.yml`).

For **interactive notebooks** or a dedicated interpreter per service, use an isolated `services/<name>/.venv` via `make venv-service SERVICE=<name>` so you do not mix multiple top-level `app` packages in one environment.

Starter notebooks live at `services/*/notebooks/explore.ipynb` (manual exploration only; **not** run in CI).

## Per-service expectations

- `services/datalake`
  - Unit: schema/helpers and data transformation logic.
  - Integration: datastore contract and migration behavior.
  - E2E: record lifecycle through canonical storage paths.
- `services/mcp-stocklake`
  - Unit: request validation, tool routing, and response shaping.
  - Integration: MCP handlers with datalake-backed operations.
  - E2E: agent workflow calls across MCP boundary.
- `services/api-gateway`
  - Unit: request/response adapters and policy utilities.
  - Integration: route wiring to internal services.
  - E2E: SaaS endpoint flow with auth and downstream dependency checks.
- `services/analytics`
  - Unit: analytics primitives and aggregation functions.
  - Integration: read contracts from datalake and output persistence/serialization.
  - E2E: analytics job input-to-output path.
- `services/screener`
  - Unit: rule evaluators and criteria-window helpers (`required_history_days`, validation warnings).
  - Integration:
    - canonical persistence boundary (seeded canonical tables/parquet -> screener engine output contract)
    - current-price HTTP boundary (market-live adapter request/response handling)
  - E2E:
    - `POST /screen/run` request-to-result path
    - evidence-field presence in screened output
    - `POST /screen/validate` and `GET /screen/presets` workflow contract

## Coverage expectations

- Baseline target (early phase): 70% line coverage per service once implementation begins.
- Preferred target (stabilization phase): 80%+ line coverage for critical paths.
- Non-negotiable:
  - all bug fixes include regression tests
  - new externally visible behavior includes at least one integration or E2E assertion
  - test fixtures should stay deterministic and prefer real seeded data over heavy mocking
