#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

ENV_FILE="$ROOT_DIR/.env"
COMPOSE_WRAPPER="$ROOT_DIR/scripts/dev-compose.sh"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "Missing .env at repository root."
  echo "Run: cp .env.example .env"
  exit 1
fi

if [[ ! -x "$COMPOSE_WRAPPER" ]]; then
  echo "Missing executable compose wrapper at scripts/dev-compose.sh"
  exit 1
fi

NO_OPENCLAW=0
SKIP_BUILD=0

for arg in "$@"; do
  case "$arg" in
    --no-openclaw)
      NO_OPENCLAW=1
      ;;
    --skip-build)
      SKIP_BUILD=1
      ;;
    *)
      echo "Unknown argument: $arg"
      echo "Supported: --no-openclaw --skip-build"
      exit 1
      ;;
  esac
done

compose_up() {
  local -a services=("postgres" "datalake" "market-live" "api-gateway" "mcp-market-live")
  if [[ "$SKIP_BUILD" -eq 1 ]]; then
    "$COMPOSE_WRAPPER" up -d "${services[@]}"
  else
    "$COMPOSE_WRAPPER" up -d --build "${services[@]}"
  fi
}

wait_for_url() {
  local url="$1"
  local max_attempts="${2:-40}"
  local sleep_seconds="${3:-2}"
  local attempt=1

  until curl -fsS "$url" >/dev/null 2>&1; do
    if [[ "$attempt" -ge "$max_attempts" ]]; then
      echo "Health check failed for $url after $max_attempts attempts."
      return 1
    fi
    attempt=$((attempt + 1))
    sleep "$sleep_seconds"
  done
}

echo "Starting core platform services..."
compose_up

echo "Waiting for service health endpoints..."
wait_for_url "http://localhost:8000/health"
wait_for_url "http://localhost:8001/health"
wait_for_url "http://localhost:8080/health"
echo "Core services are healthy."

if [[ "$NO_OPENCLAW" -eq 1 ]]; then
  echo "Skipping OpenClaw launch (--no-openclaw)."
  exit 0
fi

# shellcheck disable=SC1090
set -a
source "$ENV_FILE"
set +a

OPENCLAW_IMAGE="${OPENCLAW_IMAGE:-ghcr.io/openclaw/openclaw:latest}"
OPENCLAW_CONTAINER_NAME="${OPENCLAW_CONTAINER_NAME:-openclaw-dev}"
OPENCLAW_EXTRA_ARGS="${OPENCLAW_EXTRA_ARGS:-}"

echo "Launching OpenClaw container: $OPENCLAW_CONTAINER_NAME"
docker rm -f "$OPENCLAW_CONTAINER_NAME" >/dev/null 2>&1 || true

docker run -d \
  --name "$OPENCLAW_CONTAINER_NAME" \
  --network infra_default \
  --env-file "$ENV_FILE" \
  -e DATALAKE_BASE_URL="http://datalake:8000" \
  -e MARKET_LIVE_BASE_URL="http://market-live:8001" \
  -e API_GATEWAY_BASE_URL="http://api-gateway:8080" \
  -v "$ROOT_DIR/openclaw/skills:/workspace/skills:ro" \
  $OPENCLAW_EXTRA_ARGS \
  "$OPENCLAW_IMAGE"

echo "OpenClaw started."
echo "Container: $OPENCLAW_CONTAINER_NAME"
echo "Image: $OPENCLAW_IMAGE"
echo
echo "Inspect logs:"
echo "  docker logs -f $OPENCLAW_CONTAINER_NAME"
