# Architecture Overview

This repository is organized as a service-oriented monorepo for a stock platform, with agent-first workflows prioritized before web UX investments.

## Service roles

- `services/datalake`: system of record for canonical market, portfolio, and derived domain data.
- `services/market-live`: live market-data service for current/latest bars fetched from providers.
- `services/mcp-stocklake`: agent-facing MCP interface for OpenClaw; mediates controlled access to datalake-backed operations.
- `services/mcp-market-live`: agent-facing MCP interface for OpenClaw; mediates live/current market reads.
- `services/api-gateway`: SaaS facade for external consumers; exposes stable HTTP APIs and routes traffic to internal services.
- `services/analytics`: independent service for analysis and derived insights.
- `services/screener`: independent service for screening workflows and candidate selection.

## Interaction model

1. OpenClaw agents call `mcp-stocklake`.
2. OpenClaw agents call `mcp-market-live` for live current bars.
3. `mcp-stocklake` reads/writes through `datalake` contracts.
4. `mcp-market-live` reads current bars through `market-live`.
5. SaaS clients call `api-gateway`.
6. `api-gateway` routes canonical/historical calls to `datalake` and live/current calls to `market-live`.
7. `analytics` and `screener` consume canonical data from `datalake`.

## Deployment topology (current phase)

- Postgres runs in its own container as the platform system-of-record datastore.
- OpenClaw runs in a separate container.
- The platform service layer runs in a single service-stack container for this phase, with internal module boundaries kept strict so services can be split into separate containers later with minimal refactoring.
- Database runtime is not embedded in service containers.

## Product sequencing

Web UX is intentionally deferred until agentic workflows are validated in production-like conditions. During this phase, architecture emphasizes:

- clear service boundaries
- data contract stability
- testable service seams
