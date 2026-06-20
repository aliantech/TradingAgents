# Phase 8 Slice 3 Manual Real-Runner Smoke Command Plan

**Goal:** Add a guarded manual smoke command for operator-triggered real TradingAgents research execution.

**Scope:** Backend CLI, safe shell wrapper, focused tests, and operations documentation. The smoke remains manual and is not added to CI or scheduling.

## Tasks

- [x] Add a backend analysis CLI with a `real-runner-smoke` command.
- [x] Require the explicit runner mode gate before invoking the real runner.
- [x] Require an explicit operator confirmation flag.
- [x] Check provider prerequisites by environment variable presence only, without printing values.
- [x] Route runner exceptions through the existing adapter sanitizer.
- [x] Add focused tests that mock the runner and prove gate behavior.
- [x] Add a shell wrapper that does not source `.env` or print environment variables.
- [x] Document manual smoke usage and safety boundaries.

## Verification

- Backend focused tests:
  - `tests/test_analysis_cli_real_runner_smoke.py`
  - `tests/test_phase8_real_runner_smoke_script.py`
- Manual smoke instructions are documented in `docs/operations/phase-8-real-runner-smoke.md`.
- Safety grep confirms the new smoke path does not read or print secrets and does not introduce live trading controls.

## Non-Goals

- No automated provider calls.
- No CI live provider smoke.
- No broker integration.
- No live execution or paper-to-live workflow.
