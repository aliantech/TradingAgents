#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="${ROOT_DIR}/backend"

SYMBOL="${1:-SPY}"
ANALYSIS_DATE="${2:-2026-06-20}"
ASSET_TYPE="${3:-etf}"

cd "${BACKEND_DIR}"

if [[ -d ".venv" ]]; then
  # shellcheck disable=SC1091
  . ".venv/bin/activate"
fi

python -m app.analysis.cli real-runner-smoke \
  --symbol "${SYMBOL}" \
  --analysis-date "${ANALYSIS_DATE}" \
  --asset-type "${ASSET_TYPE}" \
  --i-understand-this-calls-a-real-llm-provider
