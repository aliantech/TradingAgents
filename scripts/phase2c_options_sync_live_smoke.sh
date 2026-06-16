#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="${ROOT_DIR}/backend"

UNDERLYING="${1:-SPX}"
EXPIRY="${2:-2026-06-19}"
LIMIT="${3:-250}"

cd "${BACKEND_DIR}"

if [[ -d ".venv" ]]; then
  # shellcheck disable=SC1091
  . ".venv/bin/activate"
fi

PYTHON_BIN="python"
if ! command -v "${PYTHON_BIN}" >/dev/null 2>&1 && command -v python3 >/dev/null 2>&1; then
  PYTHON_BIN="python3"
fi

"${PYTHON_BIN}" -m app.options.cli sync-chain \
  --underlying "${UNDERLYING}" \
  --expiry "${EXPIRY}" \
  --provider polygon \
  --limit "${LIMIT}"
