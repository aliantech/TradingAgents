# Phase 8 Slice 5 Runner Failure Diagnostics Plan

**Goal:** Improve failed/no-report diagnosis for provider, model, runtime, and report-quality errors.

**Scope:** Backend failure diagnostics derived from existing progress events, API response fields, Runs UI display, focused tests, and mocked browser smoke. The retry action remains explicit and user-controlled.

## Tasks

- [x] Add normalized failure categories for provider, model, runtime, report quality, and unknown errors.
- [x] Reuse existing TradingAgents error sanitization for diagnostic messages.
- [x] Expose derived diagnostics on analysis status and analysis run-list responses without changing persistence schema.
- [x] Show category, failed step, and retry guidance in the Runs table and detail panel.
- [x] Keep retry as an explicit button; do not auto-retry failed runs.
- [x] Add backend tests for classification and redaction.
- [x] Extend mocked browser smoke to cover diagnostics visibility.

## Verification

- Ubuntu temp copy focused backend tests:
  - `tests/test_analysis_diagnostics.py`
  - `tests/test_analysis_api_persistence.py`
  - `tests/test_tradingagents_adapter.py`
- Ubuntu temp copy backend full regression.
- Ubuntu temp copy frontend production build.
- Ubuntu temp copy mocked analysis observability browser smoke.

## Non-Goals

- No automatic retry loop.
- No scheduled provider-backed research jobs.
- No broker integration.
- No live execution or paper-to-live workflow.
