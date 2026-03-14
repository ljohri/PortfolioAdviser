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

To run the datalake API container against Postgres:

```bash
docker compose -f infra/docker-compose.yml up --build -d datalake postgres
```

Verify the API is healthy:

```bash
curl http://localhost:8000/health
```

### Stop and cleanup

Stop containers:

```bash
docker compose -f infra/docker-compose.yml down
```

Stop containers and remove volumes (including Postgres data):

```bash
docker compose -f infra/docker-compose.yml down -v
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
