# PortfolioAdviser

Initial monorepo scaffold for a stock platform with agentic and SaaS-facing service boundaries.

## Quickstart

From repository root:

```bash
cp .env.example .env
make up-core
make migrate-datalake
make smoke-live
```

## Repository layout

```text
services/
  datalake/
  market-live/
  mcp-stocklake/
  mcp-market-live/
  api-gateway/
  analytics/
  screener/
openclaw/skills/stocklake/
openclaw/skills/market-live/
docs/
infra/
.github/workflows/
.cursor/rules/
```

## Architecture at a glance

- `datalake` is the system of record.
- `market-live` handles current/latest market bars from provider APIs.
- `mcp-stocklake` is the OpenClaw/agent-facing MCP interface.
- `mcp-market-live` is the OpenClaw/agent-facing MCP interface for current/live bars.
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

### Environment configuration

From repository root:

```bash
cp .env.example .env
```

Notes:

- `.env.example` is the canonical variable contract for local development.
- Docker Compose reads `.env` for variable substitution.
- Local Python runs (`pytest`, `python -m mcp_stocklake`, `python -m mcp_market_live`, etc.) use the same variables.
- Keep real secrets in uncommitted `.env` for local work.
- Do not duplicate secrets in `infra/docker-compose.yml`; reference them with `${VAR}`.
- Keep Docker-only topology values (for example container hostnames) in Compose.

### Start local dependencies

From repository root:

```bash
make up-core
```

Equivalent wrapper command (always uses root `.env` explicitly):

```bash
./scripts/dev-compose.sh up -d --build postgres datalake market-live api-gateway
```

Verify the API is healthy:

```bash
curl http://localhost:8000/health
```

### Stop and cleanup

Stop containers:

```bash
make down
```

Stop containers and remove volumes (including Postgres data):

```bash
make down-volumes
```

Inspect running services:

```bash
make ps
```

Run datalake migrations from the container:

```bash
make migrate-datalake
```

Run API gateway smoke checks:

```bash
make smoke
```

Run strict live/provider smoke checks (requires `TIINGO_API_TOKEN`):

```bash
make smoke-live
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
