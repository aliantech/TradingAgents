# Phase 8 Roadmap

## Objective

Phase 8 turns the Phase 7 research execution path into an operable research workflow.

The immediate goal is to make deterministic and gated real TradingAgents runs easier to configure, diagnose, manually smoke, and audit without expanding into live trading.

This phase is not a live-trading phase. It does not add broker order placement, broker credentials, broker account mutation, AI-directed live trading, trading-scope MCP tools, live-trading UI controls, or automatic paper-to-live promotion.

## Entry State

Phase 7 completed research execution integration:

- Typed TradingAgents adapter contract.
- Deterministic local research runner fixture.
- Runtime-gated real TradingAgents runner path.
- Analysis API can persist completed Chinese-first reports.
- Failed/no-report states remain explicit.
- Analysis and Runs UI expose report links and progress details.
- Completion audit: `docs/roadmap/phase-7-completion-audit.md`.

Known operational gaps:

- Real provider-backed runner smoke is documented only at a high level and remains manual.
- Runtime settings expose the real-runner gate, but the UI does not yet clearly explain runner mode, provider readiness, and safe manual-smoke prerequisites.
- Report quality validation is structural, not yet product-quality oriented.
- Runner failures are persisted as progress messages, but there is no focused operations checklist for diagnosis and rollback.

## Design Principles

- Research operations before new trading behavior.
- Keep deterministic mode as the default.
- Make provider-backed execution opt-in, visible, and reversible.
- Prefer manual smoke readiness before background jobs or scheduling.
- Never require secrets in automated tests.
- Never read, print, store, or expose secret values in logs, reports, tests, or docs.
- Live broker execution remains out of scope.

## Phase 8 Slices

### Slice 1: Phase 8 Roadmap and Operations Boundary

Status: planned.

Goal:

- Define the research-operations hardening phase and preserve the no-live-trading boundary.

Deliverables:

- Phase 8 roadmap.
- Slice 1 implementation plan.
- Project status update marking Phase 8 as research operations hardening.
- Yasin Brain log entry recording that provider-backed research remains gated and live execution remains out of scope.

Verification:

- Documentation points Phase 8 to research operations and manual real-runner readiness.
- Documentation keeps broker credentials, broker account mutation, trading-scope MCP tools, live-trading UI controls, and paper-to-live promotion out of scope.
- No runtime code is added in Slice 1.

### Slice 2: Runner Mode Settings UX

Status: implemented and verified.

Goal:

- Make deterministic versus real TradingAgents runner mode visible and editable in Settings using existing persisted settings APIs.

Expected coverage:

- Runner mode, provider, deep/quick models, output language, selected analysts, and debate rounds appear in the model/agent settings section.
- UI copy explains deterministic default and real-runner prerequisites.
- Secret values are not displayed.
- Saving settings refreshes runtime configuration through the existing settings flow.

Verification:

- Frontend build passes.
- Settings catalog tests cover the new runner settings.
- Browser smoke or focused UI test covers runner-mode visibility without provider calls.

Implemented:

- `frontend/src/features/settings/settingsCatalog.ts`.
- `frontend/src/app/App.tsx`.
- `frontend/src/i18n/index.ts`.
- `frontend/src/features/settings/settingsCatalog.test.ts`.
- `frontend/e2e/settings-runner-mode-smoke.spec.ts`.
- `docs/superpowers/plans/2026-06-20-aquantlens-us-phase-8-slice-2-runner-settings-ux.md`.

Verification completed:

- Local settings catalog test passed.
- Ubuntu temp-copy settings catalog test passed.
- Ubuntu temp-copy frontend build passed.
- Ubuntu temp-copy settings runner-mode browser smoke passed: 1 test.

### Slice 3: Manual Real-Runner Smoke Command

Status: implemented and verified.

Goal:

- Add a guarded manual smoke command or documented script for operator-triggered real TradingAgents research execution.

Expected coverage:

- Requires explicit runtime gate.
- Refuses to run unless provider prerequisites are intentionally configured.
- Redacts errors through the existing adapter error path.
- Produces clear pass/fail output without printing secrets.

Verification:

- Automated tests mock the real runner and prove gate behavior.
- Manual smoke instructions are documented but not run automatically.
- Safety grep proves no secrets are read or printed by tests/docs.

Implemented:

- `backend/app/analysis/cli.py`.
- `backend/tests/test_analysis_cli_real_runner_smoke.py`.
- `backend/tests/test_phase8_real_runner_smoke_script.py`.
- `scripts/phase8_real_runner_smoke.sh`.
- `docs/operations/phase-8-real-runner-smoke.md`.
- `docs/superpowers/plans/2026-06-20-aquantlens-us-phase-8-slice-3-real-runner-smoke.md`.

Verification completed:

- Ubuntu temp-copy focused tests passed: 7 tests.
- Ubuntu temp-copy backend full regression passed: 242 tests.
- Ubuntu temp-copy manual CLI not-ready path returned `status=not_ready` before any provider call.
- Manual smoke instructions are documented and remain operator-triggered only.

### Slice 4: Report Quality Contract

Status: implemented and verified.

Goal:

- Add a lightweight report-quality validation layer for required Chinese-first sections, evidence labels, confidence bounds, and no-trading-authority language.

Expected coverage:

- Deterministic and real-runner mapped reports pass structural quality checks.
- Invalid reports fail before persistence or are persisted as failed/no-report with clear progress errors.
- Checks stay product-quality oriented and do not attempt investment correctness.

Verification:

- Backend unit tests cover valid and invalid report payloads.
- Existing analysis API tests still pass.

Implemented:

- `backend/app/reports/quality.py`.
- `backend/tests/test_report_quality.py`.
- `backend/app/analysis/tradingagents_adapter.py` now validates mapped reports before returning them for persistence.
- `backend/app/analysis/service.py` persists invalid mapped reports as failed/no-report runs with a `report_quality` progress event.
- `backend/tests/test_analysis_api_persistence.py` covers invalid report rejection before persistence.
- `docs/superpowers/plans/2026-06-20-aquantlens-us-phase-8-slice-4-report-quality-contract.md`.

Verification completed:

- Ubuntu temp-copy focused report quality/adapter/analysis/runner tests passed: 21 tests.
- Ubuntu temp-copy backend full regression passed: 248 tests.

### Slice 5: Runner Failure Diagnostics

Status: planned.

Goal:

- Improve failed/no-report diagnosis for provider/model/runtime errors.

Expected coverage:

- Normalized failure categories.
- Sanitized messages.
- Runs UI shows category, failed step, and retry guidance.
- Retry remains explicit and user-controlled.

Verification:

- Backend tests cover categorized errors and redaction.
- Frontend build and mocked browser smoke pass.

### Slice 6: Phase 8 Completion Audit

Status: planned.

Goal:

- Audit Phase 8 and record residual risks.

Verification:

- Focused runner/settings/report-quality tests pass.
- Full backend regression passes.
- Frontend build passes.
- Browser smoke passes for changed UI.
- Safety grep confirms no live-execution boundary violations.
- Project docs and Yasin Brain record completion and remaining live-execution boundary.

## Explicit Non-Goals

- Live broker order placement.
- Broker credential storage or mutation.
- Broker account balance sync.
- Broker order status sync.
- AI-direct live trading authority.
- Trading-scope MCP tools that can reach a broker.
- Live-trading UI controls.
- Automatic paper-to-live promotion.
- Scheduled provider-backed research jobs.
- Production-grade distributed job orchestration.
- Public multi-user SaaS execution.

## Completion Criteria

Phase 8 is complete only when:

- Runner mode and real-runner prerequisites are visible and editable through existing settings UX.
- Manual real-runner smoke is guarded, documented, and test-covered without automated provider calls.
- Report-quality validation exists for structural Chinese-first research output.
- Runner failures are categorized, redacted, and visible in the Runs UI.
- Focused tests, full backend regression, frontend build, and relevant browser smoke pass.
- Safety grep confirms no live-execution boundary violations.
- Project docs and Yasin Brain record that live execution remains out of scope.
