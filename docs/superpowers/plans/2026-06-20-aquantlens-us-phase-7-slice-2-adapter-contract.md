# Phase 7 Slice 2 TradingAgents Adapter Contract Plan

> **For agentic workers:** This slice defines the backend contract boundary only. Do not wire the analysis service to runtime execution in this slice.

**Goal:** Add a typed adapter contract that maps existing analysis requests into TradingAgents research execution input and maps completed TradingAgents research output back into the existing report schema.

**Architecture:** Keep FastAPI analysis persistence and report schemas as the product boundary. The adapter is deterministic and side-effect free so later slices can plug in fixture and real runners without changing the public API contract.

---

## File Structure

- Create: `backend/app/analysis/tradingagents_adapter.py`
  - Define request/result payload models.
  - Convert `AnalysisRequest` into a normalized TradingAgents execution request.
  - Convert TradingAgents report payloads into `ResearchReport`.
  - Sanitize provider/runtime errors into `AnalysisProgressEvent`.
- Create: `backend/tests/test_tradingagents_adapter.py`
  - Cover request mapping.
  - Cover report mapping.
  - Cover error sanitization.
  - Cover absence of broker/live execution public surface.
- Modify: `docs/roadmap/phase-7-roadmap.md`
  - Mark Slice 2 complete and record verification.
- Modify: `PROJECT.md`
  - Update Phase 7 progress snapshot.
- Modify: `/Users/yasin/Documents/Yasin AI OS/04-Projects/aquantlens/LOG.md`
  - Record Slice 2 implementation for the separate US/options branch.

## Assumptions

- The adapter should not call TradingAgents yet; Slice 3 will add a deterministic runner fixture and service integration.
- Existing `AnalysisRequest` and `ResearchReport` schemas are the correct API and persistence boundary.
- Error messages may include provider/runtime details, so sanitization must redact obvious key/token/password patterns.

## Safety Boundary

This slice must not add:

- Broker SDKs.
- Broker credentials.
- Broker account mutation.
- Live order methods.
- AI-directed live trading.
- Trading-scope MCP tools.
- Live-trading UI controls.
- Paper-to-live promotion.
- Provider calls in automated tests.

## Tasks

- [x] Add typed TradingAgents adapter request/result payloads.
- [x] Map analysis request fields into normalized runtime config.
- [x] Map adapter report payload into existing `ResearchReport`.
- [x] Sanitize provider/runtime errors into progress events.
- [x] Add focused unit tests.
- [x] Update roadmap and project docs.
- [x] Update Yasin Brain log.

## Verification

- `python3 -m py_compile backend/app/analysis/tradingagents_adapter.py backend/tests/test_tradingagents_adapter.py`
- Ubuntu temp copy: `PYTHONPATH=. /home/yasin/workspace/TradingAgents/backend/.venv/bin/python -m pytest tests/test_tradingagents_adapter.py tests/test_analysis_repository.py tests/test_analysis_api_persistence.py -q`
  - Result: 13 passed.
- Ubuntu temp copy: `PYTHONPATH=. /home/yasin/workspace/TradingAgents/backend/.venv/bin/python -m pytest -q`
  - Result: 229 passed.
