# Phase 7 Slice 3 Deterministic Research Runner Fixture Plan

> **For agentic workers:** This slice connects the analysis API to a deterministic local research runner fixture only. Do not call external model providers or broker systems.

**Goal:** Exercise the TradingAgents adapter boundary through the existing analysis API, repository, and report persistence path without external provider calls.

**Architecture:** `start_analysis` builds the Slice 2 adapter execution request, invokes a deterministic fixture runner, maps the result into the existing `ResearchReport` schema, and saves the completed run through `AnalysisRepository`. A controlled fixture failure path preserves failed/no-report behavior.

---

## File Structure

- Create: `backend/app/analysis/deterministic_runner.py`
  - Return deterministic Chinese-first research output through `TradingAgentsRunResult`.
  - Raise a controlled fixture error for `FAIL` to verify failed/no-report behavior.
- Modify: `backend/app/analysis/service.py`
  - Build the TradingAgents execution request.
  - Persist completed fixture reports through the existing run repository.
  - Sanitize runner errors into progress events and persist failed/no-report runs.
- Modify: `backend/tests/test_analysis_api_persistence.py`
  - Cover completed analysis status and persisted report retrieval.
  - Cover deterministic failure with no report.
  - Confirm sample/mock evidence labels are not emitted.
- Modify: `backend/tests/test_analysis_retry_api.py`
  - Cover retry behavior after manually persisted failure and generated fixture failure.
- Modify: `docs/roadmap/phase-7-roadmap.md`
  - Mark Slice 3 complete and record verification.
- Modify: `PROJECT.md`
  - Update current Phase 7 status.
- Modify: `/Users/yasin/Documents/Yasin AI OS/04-Projects/aquantlens/LOG.md`
  - Record Slice 3 implementation for the separate US/options branch.

## Assumptions

- The deterministic fixture is a temporary execution harness for API, persistence, and report contract verification.
- Real TradingAgents/provider execution remains deferred to Slice 4 behind an explicit runtime gate.
- The existing API response can continue returning HTTP 202 with `status: queued`; authoritative completion/failure is inspected through the status endpoint and reports API.

## Safety Boundary

This slice must not add:

- External model/provider calls.
- Broker SDKs.
- Broker credentials.
- Broker account mutation.
- Live order methods.
- AI-directed live trading.
- Trading-scope MCP tools.
- Live-trading UI controls.
- Paper-to-live promotion.

## Tasks

- [x] Add deterministic runner fixture.
- [x] Wire fixture into `start_analysis` through the adapter contract.
- [x] Persist completed analysis runs and reports through the existing repository path.
- [x] Preserve failed/no-report behavior for controlled runner errors.
- [x] Update focused API and retry tests.
- [x] Update roadmap and project docs.
- [x] Update Yasin Brain log.

## Verification

- `python3 -m py_compile backend/app/analysis/service.py backend/app/analysis/deterministic_runner.py backend/tests/test_analysis_api_persistence.py backend/tests/test_analysis_retry_api.py`
- Ubuntu temp copy: `PYTHONPATH=. /home/yasin/workspace/TradingAgents/backend/.venv/bin/python -m pytest tests/test_analysis_api_persistence.py tests/test_analysis_retry_api.py tests/test_tradingagents_adapter.py tests/test_analysis_repository.py -q`
  - Result: 16 passed.
- Ubuntu temp copy: `PYTHONPATH=. /home/yasin/workspace/TradingAgents/backend/.venv/bin/python -m pytest -q`
  - Result: 230 passed.
