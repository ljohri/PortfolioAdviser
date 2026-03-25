#!/usr/bin/env bash
# Create an isolated virtual environment under services/<name>/.venv and install
# that service in editable mode (plus shared stocklake-tiingo when required).
# Use this for JupyterLab, IDE interpreters, or ad-hoc exploration without the
# repo-root uv workspace .venv.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SERVICE="${1:-}"
if [[ -z "${SERVICE}" ]]; then
  echo "Usage: $0 <service-name>" >&2
  echo "Example: $0 datalake" >&2
  echo "Known services: datalake, market-live, mcp-stocklake, mcp-market-live, api-gateway, analytics, screener" >&2
  exit 1
fi

SVC_DIR="${ROOT}/services/${SERVICE}"
if [[ ! -d "${SVC_DIR}" ]] || [[ ! -f "${SVC_DIR}/pyproject.toml" ]]; then
  echo "error: no Python project at services/${SERVICE}" >&2
  exit 1
fi

VENV="${SVC_DIR}/.venv"
PY="${VENV}/bin/python"

if command -v uv >/dev/null 2>&1; then
  # --no-project: do not attach this venv to the repo-root uv workspace.
  # --seed: install pip/setuptools/wheel so `pip install jupyterlab` works after activate.
  uv venv --no-project --seed "${VENV}"
  install_pkg() {
    uv pip install --python "${PY}" "$@"
  }
else
  python3 -m venv "${VENV}"
  install_pkg() {
    "${PY}" -m pip install --upgrade pip
    "${PY}" -m pip install "$@"
  }
fi

case "${SERVICE}" in
  datalake|market-live)
    install_pkg -e "${ROOT}/packages/stocklake-tiingo"
    install_pkg -e "${SVC_DIR}"
    ;;
  mcp-stocklake)
    install_pkg -e "${ROOT}/packages/stocklake-tiingo"
    install_pkg -e "${ROOT}/services/datalake"
    install_pkg -e "${SVC_DIR}"
    ;;
  *)
    install_pkg -e "${SVC_DIR}"
    ;;
esac

echo ""
echo "Virtual environment: ${VENV}"
echo "Activate: source services/${SERVICE}/.venv/bin/activate"
echo "Jupyter (optional): pip install jupyterlab ipykernel && python -m ipykernel install --user --name=${SERVICE} --display-name='Python (${SERVICE})'"
