#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "${ROOT_DIR}/backend"
if [[ -d ".venv" ]]; then
  # shellcheck disable=SC1091
  . ".venv/bin/activate"
fi
pytest -q

cd "${ROOT_DIR}/frontend"
npm run build

cd "${ROOT_DIR}"
if [[ "${RUN_LIVE_SMOKE:-0}" == "1" ]]; then
  scripts/phase2b_final_live_smoke.sh
else
  echo "Skipping live provider smoke. Set RUN_LIVE_SMOKE=1 after runtime provider env vars are available."
fi
