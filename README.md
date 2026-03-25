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
packages/
  stocklake-tiingo/    # shared Tiingo HTTP client (uv workspace member)
services/
  <name>/notebooks/    # optional explore.ipynb + extra notebooks per service
  datalake/
  market-live/
  mcp-stocklake/
  mcp-market-live/
  api-gateway/
  analytics/
  screener/
scripts/               # e.g. bootstrap-service-venv.sh, dev-compose.sh, smoke_gateway.py
web/
openclaw/skills/stocklake/
openclaw/skills/market-live/
docs/
infra/
.github/workflows/
.cursor/rules/
pyproject.toml         # uv workspace root (members + uv.lock)
```

Each Python service may include `services/<name>/notebooks/explore.ipynb` for API exploration (Jupyter); add more `.ipynb` files in the same directory as needed.

## Documentation index

| Topic | Where |
|--------|--------|
| Service roles and interaction model | [`docs/architecture.md`](docs/architecture.md) |
| End-to-end platform + diagrams | [`docs/overall-architecture.md`](docs/overall-architecture.md) |
| Public HTTP contract (`api-gateway` /v1) | [`docs/service-contracts.md`](docs/service-contracts.md) |
| uv workspace, pytest, notebooks vs CI | [`docs/testing-strategy.md`](docs/testing-strategy.md) |
| Run MCP servers + OpenClaw JSON snippet | [`docs/openclaw-integration.md`](docs/openclaw-integration.md) |
| Docker OpenClaw bring-up script | [`docs/openclaw-bringup-and-connection.md`](docs/openclaw-bringup-and-connection.md) |

## Architecture at a glance

- `packages/stocklake-tiingo` is the shared Tiingo HTTP client library used by `datalake` and `market-live` (uv workspace package).
- `datalake` is the system of record.
- `market-live` handles current/latest market bars from provider APIs.
- `mcp-stocklake` is the OpenClaw/agent-facing MCP interface.
- `mcp-market-live` is the OpenClaw/agent-facing MCP interface for current/live bars.
- `api-gateway` is the SaaS facade.
- `analytics` and `screener` are separate services with independent responsibilities.
- `web` consumes `api-gateway` only and does not call `datalake` directly.

## Local development (scaffold phase)

### Prerequisites

- Docker + Docker Compose
- Python 3.11+
- [uv](https://docs.astral.sh/uv/) (for `datalake`, `market-live`, and `mcp-stocklake`, which share the `stocklake-tiingo` workspace package)

Workspace members use a repo-root `pyproject.toml` and `uv.lock`. From the repository root, sync and run tests for one package, for example:

```bash
uv sync --package stocklake-datalake
uv run --package stocklake-datalake python -m pytest services/datalake/tests -q
```

Use `stocklake-market-live` or `stocklake-mcp-stocklake` similarly. For local MCP bring-up that needs both datalake code paths and `mcp-stocklake`, run `uv sync` for both `stocklake-datalake` and `stocklake-mcp-stocklake` (see `docs/openclaw-integration.md`). Other services under `services/` can still be installed with `pip install ./services/<name>` in a virtual environment.

### Per-service virtual environments (Jupyter / exploration)

CI and reproducible installs use the **repo-root** uv workspace (single `uv.lock`). For **interactive** work—JupyterLab, Conda/Anaconda-connected kernels, or a dedicated IDE interpreter per service—use a **separate** environment in that service’s directory:

```bash
make venv-service SERVICE=datalake
# or: ./scripts/bootstrap-service-venv.sh datalake
source services/datalake/.venv/bin/activate
```

This creates `services/<name>/.venv`, installs `packages/stocklake-tiingo` when needed (`datalake`, `market-live`, `mcp-stocklake`), and for `mcp-stocklake` also installs editable `datalake` so `app.*` imports resolve. Other services only install their own package.

**JupyterLab** (or any notebook UI) inside that environment:

```bash
pip install jupyterlab ipykernel httpx
python -m ipykernel install --user --name=datalake --display-name="Python (datalake)"
cd services/datalake/notebooks
jupyter lab
```

Open **`explore.ipynb`** in that folder as the starter template for HTTP exploration; add more notebooks alongside it as needed. Repeat per service (`services/<name>/notebooks/explore.ipynb`).

If `pip` is missing in the venv, reinstall with `./scripts/bootstrap-service-venv.sh` (when `uv` is used, the venv is created with `--seed` so `pip` is present), or from the repo root run `uv pip install --python services/<name>/.venv/bin/python jupyterlab ipykernel`.

Use a **different kernel name per service** so notebooks do not share one `app` package across incompatible services. If you use **Anaconda**, create or select an env, then run the same `pip install -e` lines as the script (or run the script from a terminal where `python3` is your desired base).

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

Bring up OpenClaw plus connected services (automated helper):

```bash
./scripts/bringup-openclaw.sh
```

### Run tests

**Workspace members** (`datalake`, `market-live`, `mcp-stocklake`): from repository root, use uv so `stocklake-tiingo` resolves:

```bash
uv sync --package stocklake-datalake
uv run --package stocklake-datalake python -m pytest services/datalake/tests -q
```

Repeat with `stocklake-market-live` / `services/market-live/tests` and `stocklake-mcp-stocklake` / `services/mcp-stocklake/tests`. Use `python -m pytest` (not a bare `pytest` shim) so the package venv is used.

**Other services** (for example `api-gateway`, `analytics`, `screener`): create a venv, `pip install ./services/<name>`, then `pytest services/<name>/tests -q`.

To run everything locally, run the three uv blocks above plus pip-based services; CI encodes the same split (`.github/workflows/ci.yml`).

## Notes

- Business logic lives in **service layers** (not route handlers); keep storage behind repositories. See `.cursor/rules/` for AI-facing conventions.
- **CI** runs Python tests per service (`.github/workflows/ci.yml`): uv for workspace members, `pip install` for the rest.
- **Docker**: `datalake` and `market-live` build from the **repo root** so `stocklake-tiingo` is included (`infra/docker-compose.yml`).
