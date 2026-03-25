# Architecture Overview

This repository is organized as a service-oriented monorepo for a stock platform, with agent-first workflows prioritized before web UX investments.

## Shared Python packages

- `packages/stocklake-tiingo`: shared Tiingo HTTP client (`TiingoClient`) used by `datalake` and `market-live`. Each service keeps a thin `app.services.tiingo_client` shim that re-exports the library so imports and tests stay stable. Dependency versions for workspace members are pinned via a repo-root [uv](https://docs.astral.sh/uv/) workspace (`pyproject.toml`, `uv.lock`).
- **Local exploration:** developers may also create **one virtual environment per service** under `services/<name>/.venv` (see `scripts/bootstrap-service-venv.sh` and the root `README`) for JupyterLab, Anaconda-linked kernels, or per-service IDE interpreters. That is separate from the root uv workspace used for CI and `uv lock`. Optional **`services/<name>/notebooks/explore.ipynb`** templates document HTTP calls against that service (or its upstream, for MCP servers); they are not part of automated test runs.

## Service roles

- `services/datalake`: system of record for canonical market, portfolio, and derived domain data.
- `services/market-live`: live market-data service for current/latest bars fetched from providers.
- `services/mcp-stocklake`: agent-facing MCP interface for OpenClaw; mediates controlled access to datalake-backed operations.
- `services/mcp-market-live`: agent-facing MCP interface for OpenClaw; mediates live/current market reads.
- `services/api-gateway`: SaaS facade for external consumers; exposes stable HTTP APIs and routes traffic to internal services.
- `services/analytics`: independent service for analysis and derived insights.
- `services/screener`: independent service for screening workflows and candidate selection.
- `web`: user-facing application layer that consumes `api-gateway` APIs.

## Interaction model

1. OpenClaw agents call `mcp-stocklake`.
2. OpenClaw agents call `mcp-market-live` for live current bars.
3. `mcp-stocklake` reads/writes through `datalake` contracts.
4. `mcp-market-live` reads current bars through `market-live`.
5. SaaS clients call `api-gateway`.
6. `api-gateway` routes canonical/historical calls to `datalake` and live/current calls to `market-live`.
7. `analytics` and `screener` consume canonical data from `datalake`.
8. `web` consumes `api-gateway` and does not call `datalake` directly.

## Deployment topology (current phase)

- Postgres runs in its own container as the platform system-of-record datastore.
- OpenClaw runs in a separate container.
- Each Python service (`datalake`, `market-live`, `api-gateway`, `mcp-market-live`, and placeholders for others) has its own image/container in Compose, with strict internal module boundaries so processes can be rescheduled or scaled independently later.
- `datalake` and `market-live` images build from the **repository root** so they can install `packages/stocklake-tiingo` alongside the service package (see `infra/docker-compose.yml` and service Dockerfiles).
- Database runtime is not embedded in service containers.

## Product sequencing

Web UX is intentionally deferred until agentic workflows are validated in production-like conditions. During this phase, architecture emphasizes:

- clear service boundaries
- data contract stability
- testable service seams
