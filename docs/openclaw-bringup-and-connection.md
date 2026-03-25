# OpenClaw Bring-up and System Connection

This guide explains how to bring up OpenClaw in Docker and connect it to the currently running platform services.

## What this automates

The provided script automates the following:

1. validates root `.env` exists
2. starts required service containers
3. waits for key health endpoints
4. launches OpenClaw container on the same Docker network
5. mounts skills from `openclaw/skills`

## Prerequisites

- Docker and Docker Compose
- root `.env` file (copy from `.env.example`)
- optional: `OPENCLAW_IMAGE` set in shell or `.env` (if omitted, default is used)

To run MCP servers on the host (outside Docker), see **`docs/openclaw-integration.md`** for uv workspace setup and environment variables.

## Automated bring-up (recommended)

From repository root:

```bash
./scripts/bringup-openclaw.sh
```

Defaults used by the script:

- core services started:
  - `postgres`
  - `datalake`
  - `market-live`
  - `api-gateway`
  - `mcp-market-live`
- expected service health:
  - `http://localhost:8000/health`
  - `http://localhost:8001/health`
  - `http://localhost:8080/health`
- OpenClaw container network:
  - `infra_default`

## OpenClaw connection values inside Docker network

When OpenClaw runs in Docker on `infra_default`, use container DNS names:

- `DATALAKE_BASE_URL=http://datalake:8000`
- `MARKET_LIVE_BASE_URL=http://market-live:8001`
- `API_GATEWAY_BASE_URL=http://api-gateway:8080`

The script injects these values automatically into the OpenClaw container.

## Skill mounting

The script mounts repository skills read-only:

- host: `openclaw/skills`
- container: `/workspace/skills`

This keeps agent behavior guidance versioned in-repo while OpenClaw runs isolated.

## Useful flags

- `--no-openclaw`
  - start and verify platform services only; do not launch OpenClaw
- `--skip-build`
  - skip image rebuild while starting compose services

Examples:

```bash
./scripts/bringup-openclaw.sh --no-openclaw
./scripts/bringup-openclaw.sh --skip-build
```

## Environment overrides

Optional runtime overrides:

- `OPENCLAW_IMAGE` (default: `ghcr.io/openclaw/openclaw:latest`)
- `OPENCLAW_CONTAINER_NAME` (default: `openclaw-dev`)
- `OPENCLAW_EXTRA_ARGS` (additional `docker run` args)

Example:

```bash
OPENCLAW_IMAGE=my-registry/openclaw:dev ./scripts/bringup-openclaw.sh
```

## Notes and current limitations

- `mcp-market-live` is containerized in the current stack.
- `mcp-stocklake` is still evolving in Docker runtime wiring; use the gateway + datalake endpoints in OpenClaw flows until MCP wiring is finalized for that path.
- this script focuses on reliable local orchestration and endpoint connectivity; tool-specific OpenClaw config remains runtime-specific.

## Teardown

Stop only OpenClaw container:

```bash
docker rm -f openclaw-dev
```

Stop full stack:

```bash
./scripts/dev-compose.sh down
```
