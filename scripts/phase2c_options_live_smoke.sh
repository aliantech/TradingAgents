#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="${ROOT_DIR}/backend"

UNDERLYINGS="${1:-SPY,SPX}"

cd "${BACKEND_DIR}"

if [[ -d ".venv" ]]; then
  # shellcheck disable=SC1091
  . ".venv/bin/activate"
fi

python -m app.options.live_smoke --underlyings "${UNDERLYINGS}"
