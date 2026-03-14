# Testing Strategy

This strategy sets minimal but clear expectations for service-level testing while the platform is in scaffold and early implementation phases.

## Test level definitions

- Unit tests: validate isolated functions/classes with no network or database dependency.
- Integration tests: validate interactions across components (for example, service + datastore contract) with controlled dependencies.
- End-to-end (E2E) tests: validate user- or agent-facing flows across multiple services from interface to persistence boundary.

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
  - Unit: screen predicates and ranking helpers.
  - Integration: canonical input data and screener output contract.
  - E2E: screening request-to-result path.

## Coverage expectations

- Baseline target (early phase): 70% line coverage per service once implementation begins.
- Preferred target (stabilization phase): 80%+ line coverage for critical paths.
- Non-negotiable:
  - all bug fixes include regression tests
  - new externally visible behavior includes at least one integration or E2E assertion
