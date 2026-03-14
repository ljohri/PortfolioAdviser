# PortfolioAdviser

Initial monorepo scaffold for a stock platform with agentic and SaaS-facing service boundaries.

## Repository layout

```text
services/
  datalake/
  mcp-stocklake/
  api-gateway/
  analytics/
  screener/
openclaw/skills/stocklake/
docs/
infra/
.github/workflows/
.cursor/rules/
```

## Architecture at a glance

- `datalake` is the system of record.
- `mcp-stocklake` is the OpenClaw/agent-facing MCP interface.
- `api-gateway` is the SaaS facade.
- `analytics` and `screener` are separate services with independent responsibilities.
- Web UX is intentionally deferred until agentic workflows are validated.

See:
- `docs/architecture.md`
- `docs/testing-strategy.md`

## Local development (scaffold phase)

### Prerequisites

- Docker + Docker Compose
- Python 3.11+

### Start local dependencies

From repository root:

```bash
docker compose -f infra/docker-compose.yml up -d postgres
```

To include placeholder service containers as needed:

```bash
docker compose -f infra/docker-compose.yml --profile placeholder up -d
```

### Run tests

Run all current service tests:

```bash
pytest services/*/tests -q
```

Run tests for a single service:

```bash
pytest services/datalake/tests -q
```

## Notes

- This scaffold intentionally excludes business logic.
- CI is configured to run Python tests per service when tests are present.
