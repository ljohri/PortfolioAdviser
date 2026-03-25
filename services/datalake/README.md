# datalake

`datalake` is the system of record for market, portfolio, and derived platform data.

Tiingo HTTP calls use the shared package `stocklake-tiingo` (see `packages/stocklake-tiingo`). This service re-exports `TiingoClient` from `app.services.tiingo_client` for a stable import path.

## Development

This project is a member of the **repo-root uv workspace**. From the repository root:

```bash
uv sync --package stocklake-datalake
uv run --package stocklake-datalake python -m pytest tests -q
```

For a **local-only** virtual environment (JupyterLab, Conda, or a fixed IDE interpreter), from the repository root:

```bash
make venv-service SERVICE=datalake
source services/datalake/.venv/bin/activate
```

## Scope (scaffold phase)

- Define canonical storage schemas and ingestion boundaries
- Expose internal data contracts to upstream/downstream services
- Keep implementation minimal until interfaces are validated

## Planned structure

- `tests/` for service-level tests
- implementation modules to be added in later phases

Docker images for this service are built with **repository root** as context so `packages/stocklake-tiingo` is available (see `infra/docker-compose.yml`).
