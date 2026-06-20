# Phase 7 Slice 4 Real TradingAgents Runner Gate Plan

> **For agentic workers:** This slice adds the gated real TradingAgents runner path. Automated tests must not call external model providers.

**Goal:** Connect the backend analysis execution boundary to the local TradingAgents graph behind an explicit runtime gate while keeping deterministic execution as the default.

**Architecture:** `start_analysis` resolves runtime settings from the existing settings database boundary, then dispatches to `run_configured_research`. The default runner mode is `deterministic`. The real TradingAgents graph is imported and invoked only when `AQUANTLENS_TRADINGAGENTS_RUNNER_MODE` resolves to `real-tradingagents`.

---

## File Structure

- Create: `backend/app/analysis/tradingagents_runner.py`
  - Dispatch deterministic versus real runner by runtime mode.
  - Build real TradingAgents config from runtime settings.
  - Invoke `TradingAgentsGraph.propagate` only behind the explicit real-runner gate.
  - Map returned TradingAgents state into the adapter result payload.
- Create: `backend/tests/test_tradingagents_runner.py`
  - Prove default deterministic mode does not call the real runner.
  - Prove the real runner refuses execution unless the runtime gate is enabled.
  - Prove real runner config reads provider/model/runtime values from settings.
  - Prove real TradingAgents state maps into the adapter result payload.
- Modify: `backend/app/analysis/service.py`
  - Resolve runtime settings from `AnalysisRepository.session`.
  - Dispatch through `run_configured_research`.
- Modify: `backend/app/core/config.py` and `backend/app/settings/runtime.py`
  - Add non-secret TradingAgents runtime settings with deterministic defaults.
- Modify: `docs/roadmap/phase-7-roadmap.md`
  - Mark Slice 4 complete and record verification.
- Modify: `PROJECT.md`
  - Update current Phase 7 status.
- Modify: `/Users/yasin/Documents/Yasin AI OS/04-Projects/aquantlens/LOG.md`
  - Record Slice 4 implementation for the separate US/options branch.

## Runtime Gate

Default:

- `AQUANTLENS_TRADINGAGENTS_RUNNER_MODE=deterministic`

Manual real-runner smoke, only when provider credentials and runtime settings are intentionally configured:

```bash
cd /path/to/TradingAgents/backend
PYTHONPATH=. AQUANTLENS_TRADINGAGENTS_RUNNER_MODE=real-tradingagents python -m pytest tests/test_tradingagents_runner.py -q
```

The command above only verifies the gate/config tests unless an operator writes a separate manual smoke that posts to `/api/analysis` with configured provider access. Do not run provider-backed analysis from automated tests.

## Safety Boundary

This slice must not add:

- Default provider calls.
- Provider calls in automated tests.
- Broker SDKs.
- Broker credentials.
- Broker account mutation.
- Live order methods.
- AI-directed live trading.
- Trading-scope MCP tools.
- Live-trading UI controls.
- Paper-to-live promotion.

## Tasks

- [x] Add real TradingAgents runner dispatch behind explicit runtime mode.
- [x] Add runtime settings for runner mode, provider, model, output language, analyst selection, and debate rounds.
- [x] Keep deterministic runner as default.
- [x] Map real TradingAgents state into existing report schema through the adapter payload.
- [x] Add focused tests proving gate behavior and config mapping without provider calls.
- [x] Update roadmap and project docs.
- [x] Update Yasin Brain log.

## Verification

- `python3 -m py_compile backend/app/analysis/tradingagents_runner.py backend/app/analysis/service.py backend/app/core/config.py backend/app/settings/runtime.py backend/tests/test_tradingagents_runner.py`
- Ubuntu temp copy: `PYTHONPATH=. /home/yasin/workspace/TradingAgents/backend/.venv/bin/python -m pytest tests/test_tradingagents_runner.py tests/test_analysis_api_persistence.py tests/test_analysis_retry_api.py tests/test_tradingagents_adapter.py -q`
  - Result: 17 passed.
- Ubuntu temp copy: `PYTHONPATH=. /home/yasin/workspace/TradingAgents/backend/.venv/bin/python -m pytest tests/test_settings_api.py tests/test_tradingagents_runner.py -q`
  - Result: 6 passed.
- Ubuntu temp copy: `PYTHONPATH=. /home/yasin/workspace/TradingAgents/backend/.venv/bin/python -m pytest -q`
  - Result: 235 passed.
