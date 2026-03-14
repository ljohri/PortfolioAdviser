# Architecture Overview

This repository is organized as a service-oriented monorepo for a stock platform, with agent-first workflows prioritized before web UX investments.

## Service roles

- `services/datalake`: system of record for canonical market, portfolio, and derived domain data.
- `services/mcp-stocklake`: agent-facing MCP interface for OpenClaw; mediates controlled access to datalake-backed operations.
- `services/api-gateway`: SaaS facade for external consumers; exposes stable HTTP APIs and routes traffic to internal services.
- `services/analytics`: independent service for analysis and derived insights.
- `services/screener`: independent service for screening workflows and candidate selection.

## Interaction model

1. OpenClaw agents call `mcp-stocklake`.
2. `mcp-stocklake` reads/writes through `datalake` contracts.
3. SaaS clients call `api-gateway`.
4. `api-gateway`, `analytics`, and `screener` consume canonical data from `datalake`.

## Product sequencing

Web UX is intentionally deferred until agentic workflows are validated in production-like conditions. During this phase, architecture emphasizes:

- clear service boundaries
- data contract stability
- testable service seams
