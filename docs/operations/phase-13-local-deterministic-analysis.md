# Phase 13 Local Deterministic Analysis

Status: Ready for local Codex-agent execution
Last Reviewed: 2026-07-01
Owner: Yasin

## Purpose

Run the stock-analysis workflow locally without configuring a large-model API key.

This path verifies the AQuantLens analysis API, TradingAgents adapter boundary, report mapping, and persistence using the deterministic fixture runner. It is not a real LLM/provider research report and does not call OpenAI, Anthropic, Google, broker APIs, or live-trading systems.

## Boundary

Use this path when the goal is to let Codex agent exercise local stock-analysis features before real provider setup.

Do not use these entries for no-provider local analysis:

- `tradingagents analyze`;
- `python main.py`;
- `scripts/phase8_real_runner_smoke.sh`;
- `python -m app.analysis.cli real-runner-smoke` with real-provider confirmation.

Those entries are tied to the real TradingAgents/provider path or the guarded real-runner smoke boundary.

## Safe Runtime Settings

Use a clean temporary SQLite database so saved runtime settings cannot accidentally force `real-tradingagents` mode:

```bash
export AQUANTLENS_DATABASE_URL=sqlite:////tmp/aquantlens-local-analysis.db
export AQUANTLENS_TRADINGAGENTS_RUNNER_MODE=deterministic
export AQUANTLENS_REALTIME_MARKET_PUBLISH_ENABLED=false
```

Do not set provider API keys for this local deterministic path.

## API Server Flow

Run the backend from the clean mirror or local checkout:

```bash
cd /home/yasin/workspace/TradingAgents/backend

AQUANTLENS_DATABASE_URL=sqlite:////tmp/aquantlens-local-analysis.db \
AQUANTLENS_TRADINGAGENTS_RUNNER_MODE=deterministic \
AQUANTLENS_REALTIME_MARKET_PUBLISH_ENABLED=false \
PYTHONPATH=. \
/home/yasin/workspace/TradingAgents/backend/.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8022
```

Submit a local deterministic analysis:

```bash
curl -s -X POST http://127.0.0.1:8022/api/analysis \
  -H 'Content-Type: application/json' \
  -d '{"symbol":"QQQ","asset_type":"etf","analysis_date":"2026-06-18","language":"zh","llm_provider":"local-fixture","model":"deterministic-tradingagents-fixture","depth":"standard","analyst_set":"macro-options","research_template":"macro-options-readthrough"}'
```

Read the status with the returned `analysis_id`:

```bash
curl -s http://127.0.0.1:8022/api/analysis/<analysis_id>
```

Read the report with the returned `report_id`:

```bash
curl -s http://127.0.0.1:8022/api/reports/<report_id>
```

Expected report evidence:

```text
deterministic-tradingagents-fixture
```

## Codex-Agent Smoke

For a non-server smoke, a Codex agent can use FastAPI `TestClient` against a temporary SQLite database:

```bash
cd /home/yasin/workspace/TradingAgents/backend
TMP_DB=/tmp/aquantlens-local-analysis-smoke.sqlite
rm -f "$TMP_DB"

AQUANTLENS_DATABASE_URL="sqlite:///$TMP_DB" \
AQUANTLENS_TRADINGAGENTS_RUNNER_MODE=deterministic \
PYTHONPATH=. \
/home/yasin/workspace/TradingAgents/backend/.venv/bin/python -c '
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)
payload = {
    "symbol": "QQQ",
    "asset_type": "etf",
    "analysis_date": "2026-06-18",
    "language": "zh",
    "llm_provider": "local-fixture",
    "model": "deterministic-tradingagents-fixture",
    "depth": "standard",
    "analyst_set": "macro-options",
    "research_template": "macro-options-readthrough",
}
response = client.post("/api/analysis", json=payload)
print("POST_STATUS", response.status_code)
print(response.json())
analysis_id = response.json()["analysis_id"]
status = client.get(f"/api/analysis/{analysis_id}")
print("STATUS", status.status_code)
print(status.json())
report_id = status.json()["report_id"]
report = client.get(f"/api/reports/{report_id}")
print("REPORT", report.status_code)
payload = report.json()
print({
    "symbol": payload["symbol"],
    "language": payload["language"],
    "summary": payload["summary"],
    "evidence_labels": payload["evidence_labels"],
    "confidence": payload["confidence"],
})
'
```

Expected result:

- `POST_STATUS 202`;
- status payload `status` is `completed`;
- report payload `evidence_labels` is `["deterministic-tradingagents-fixture"]`;
- no real-provider confirmation flag is used;
- no provider API key is required.

## Verified Result

On 2026-07-01, the Codex-agent smoke passed from the then-current `/home/yasin/workspace/TradingAgents-current/backend` checkout with a temporary SQLite database:

```text
POST_STATUS 202
STATUS 200
REPORT 200
symbol=QQQ
language=zh
evidence_labels=["deterministic-tradingagents-fixture"]
confidence=0.61
```

Focused deterministic tests also passed:

```text
tests/test_analysis_api_persistence.py tests/test_tradingagents_runner.py
15 passed in 3.78s
```

## Next Local Work

The next local-only improvement should make this deterministic path easier to run from the product surface, without adding a real-provider dependency.

Candidate next steps:

- document a UI workflow for submitting local deterministic analysis;
- add a small deterministic-only CLI wrapper for `POST /api/analysis`;
- add a local runbook for comparing deterministic outputs across `SPY`, `QQQ`, `AAPL`, `TSLA`, and `SPX`.
