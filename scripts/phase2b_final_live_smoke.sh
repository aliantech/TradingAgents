#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="${ROOT_DIR}/backend"

PROVIDER="${1:-polygon}"
SYMBOL="${2:-SPY}"
TIMEFRAME="${3:-1d}"
START_DATE="${4:-2026-06-17}"
END_DATE="${5:-2026-06-17}"

cd "${BACKEND_DIR}"

if [[ -d ".venv" ]]; then
  # shellcheck disable=SC1091
  . ".venv/bin/activate"
fi

python -m app.market_data.cli final-live-smoke-gate \
  --provider "${PROVIDER}" \
  --symbol "${SYMBOL}" \
  --timeframe "${TIMEFRAME}" \
  --start "${START_DATE}" \
  --end "${END_DATE}"
