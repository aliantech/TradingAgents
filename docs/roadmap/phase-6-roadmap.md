# Phase 6 Roadmap

## Objective

Phase 6 hardens the Phase 5 paper-only MVP into a reviewable, observable, and testable paper workflow.

The goal is not to add live execution. The goal is to make paper trading safer to operate and easier to inspect before any future live-execution discussion.

## Entry State

Phase 5 completed the approved paper-only MVP:

- Paper-only architecture and safety specification.
- Paper trading domain contracts.
- Pure RiskGuard evaluator.
- SQLAlchemy-backed persistence and append-only audit events.
- Human-facing paper intent API with idempotency and review gates.
- Local deterministic paper adapter for simulated fills, cash, and positions.
- Strategy Lab Candidate-to-Paper UI flow.

Reference completion audit: `docs/roadmap/phase-5-completion-audit.md`.

## Design Principles

- Paper-only remains the hard boundary.
- Improve observability before expanding behavior.
- Keep every paper mutation database-backed and audit-backed.
- Prefer small vertical slices that each add user-visible or operator-visible confidence.
- Browser verification should cover critical paper workflows, not decorative UI states.
- No broker SDK, broker credentials, live order methods, trading-scope MCP tools, or paper-to-live controls.

## Phase 6 Slices

### Slice 1: Phase 6 Roadmap and Safety Boundary

Status: implemented and verified on 2026-06-20.

Deliverables:

- Phase 6 roadmap.
- Slice 1 implementation plan.
- Project status update marking Phase 6 as paper workflow hardening.
- Yasin Brain log entry recording that live execution remains out of scope.

Verification:

- Documentation does not authorize live execution.
- Documentation keeps broker credentials, broker account mutation, trading-scope MCP tools, and paper-to-live promotion out of scope.
- Project status points to Phase 6 paper-only hardening.

### Slice 2: Paper Workflow Browser Smoke Test

Status: implemented and verified on 2026-06-20.

Goal:

- Add a minimal browser smoke path for Strategy Lab Candidate-to-Paper UI.

Expected coverage:

- Open Strategy Lab.
- Locate Candidate Review Board paper action.
- Confirm paper-only UI copy and absence of live-trading controls.
- Exercise the review panel against controlled API fixtures or test-backed app state.

Implementation plan:

- `docs/superpowers/plans/2026-06-20-aquantlens-us-phase-6-slice-2-paper-workflow-browser-smoke.md`

Implemented files:

- `frontend/playwright.config.ts`
- `frontend/e2e/paper-workflow-smoke.spec.ts`
- `frontend/package.json`
- `frontend/package-lock.json`

Verification:

- Ubuntu isolated clone `/tmp/tradingagents-phase6-slice2-1781937695`: `npm run e2e:paper` passed, 1 test.
- Ubuntu isolated clone `/tmp/tradingagents-phase6-slice2-1781937695`: `npm run build` passed.
- Safety grep only matched paper-only test assertions and explicit out-of-scope documentation.

### Slice 3: Paper Account and Position Summary API

Status: implemented and verified on 2026-06-20.

Goal:

- Add a compact paper account summary endpoint for UI and operator inspection.

Expected coverage:

- Cash.
- Positions.
- Open or recently handled intents.
- Recent fills.
- Recent audit events.

Implementation plan:

- `docs/superpowers/plans/2026-06-20-aquantlens-us-phase-6-slice-3-paper-account-summary-api.md`

Implemented files:

- `backend/app/paper_trading/repository.py`
- `backend/app/paper_trading/router.py`
- `backend/tests/test_paper_trading_api.py`

Verification:

- Backend tests prove summary data is account-scoped.
- Backend tests prove no broker account fields or live order fields are exposed.
- Ubuntu temp copy `/tmp/tradingagents-slice3-verify`: `/home/yasin/workspace/TradingAgents/backend/.venv/bin/python -m pytest backend/tests/test_paper_trading_api.py backend/tests/test_paper_trading_repository.py -q` passed, 19 tests.

### Slice 4: Paper PnL Snapshot

Status: implemented and verified on 2026-06-20.

Goal:

- Add paper-only unrealized/realized PnL snapshot logic using explicit caller-provided or stored reference prices.

Expected coverage:

- Equity/ETF position market value.
- Option position market value using paper reference price, not broker quote.
- Cash plus position value account equity.
- Clear stale-price or missing-price state.

Implementation plan:

- `docs/superpowers/plans/2026-06-20-aquantlens-us-phase-6-slice-4-paper-pnl-snapshot.md`

Implemented files:

- `backend/app/paper_trading/pnl.py`
- `backend/app/paper_trading/repository.py`
- `backend/app/paper_trading/router.py`
- `backend/tests/test_paper_trading_pnl.py`
- `backend/tests/test_paper_trading_api.py`

Verification:

- Pure calculation tests cover long/short-like position states that are allowed by current paper contracts.
- API tests prove PnL output does not include broker account or live execution fields.
- No external market-data fetch is introduced inside paper PnL calculation.
- Ubuntu temp copy `/tmp/tradingagents-slice4-verify`: `/home/yasin/workspace/TradingAgents/backend/.venv/bin/python -m pytest backend/tests/test_paper_trading_pnl.py backend/tests/test_paper_trading_api.py backend/tests/test_paper_trading_repository.py -q` passed, 25 tests.

### Slice 5: Paper Risk Dashboard UI

Status: implemented and verified on 2026-06-20.

Goal:

- Add a compact Strategy Lab or paper panel view for paper account exposure and recent paper workflow state.

Expected coverage:

- Cash and estimated paper equity.
- Position table.
- Recent paper intents and outcomes.
- RiskGuard rejection reason visibility.
- Audit trail preview.

Implementation plan:

- `docs/superpowers/plans/2026-06-20-aquantlens-us-phase-6-slice-5-paper-risk-dashboard-ui.md`

Implemented files:

- `frontend/src/lib/api.ts`
- `frontend/src/features/strategy-lab/StrategyLabPanel.tsx`
- `frontend/e2e/paper-workflow-smoke.spec.ts`

Verification:

- Frontend build passes.
- Browser smoke covers key visible states.
- UI copy remains paper-only.
- Ubuntu temp copy `/tmp/tradingagents-slice5-verify`: backend focused paper tests passed, 25 tests.
- Ubuntu temp copy `/tmp/tradingagents-slice5-verify/frontend`: `npm run build` passed.
- Ubuntu temp copy `/tmp/tradingagents-slice5-verify/frontend`: `npx playwright test e2e/paper-workflow-smoke.spec.ts` passed, 1 test.

### Slice 6: Phase 6 Completion Audit

Status: implemented and verified on 2026-06-20.

Goal:

- Audit Phase 6 after slices are implemented and record residual risks.

Implementation plan:

- `docs/superpowers/plans/2026-06-20-aquantlens-us-phase-6-slice-6-completion-audit.md`

Audit document:

- `docs/roadmap/phase-6-completion-audit.md`

Verification:

- Focused backend paper tests pass.
- Full backend regression passes.
- Frontend build passes.
- Browser smoke passes.
- Safety grep only matches negative tests or explicit non-goal docs.
- Project docs and Yasin Brain record completion and remaining live-execution boundary.
- Ubuntu temp copy `/tmp/tradingagents-phase6-audit`: focused paper tests passed, 85 tests.
- Ubuntu temp copy `/tmp/tradingagents-phase6-audit/backend`: full backend regression passed, 225 tests.
- Ubuntu temp copy `/tmp/tradingagents-phase6-audit/frontend`: `npm run build` passed.
- Ubuntu temp copy `/tmp/tradingagents-phase6-audit/frontend`: `npx playwright test e2e/paper-workflow-smoke.spec.ts` passed, 1 test.

## Explicit Non-Goals

- Live broker order placement.
- Broker credential storage or mutation.
- Broker account balance sync.
- Broker order status sync.
- AI-direct live trading authority.
- Trading-scope MCP tools that can reach a broker.
- Live-trading UI controls.
- Automatic promotion from paper to live.
- Production-grade backtesting engine.
- Full OPRA tick/quote archival.
- Multi-user trading operations.

## Required Safety Checks Before Any Phase 6 Implementation

Before code implementation begins, write a task-level implementation plan that includes:

- Failing tests before behavior changes.
- Exact files to create or modify.
- Explicit no-broker grep checks.
- Ubuntu verification commands.
- Browser verification commands when UI changes.
- Documentation update steps.
- A final audit section that confirms paper-only scope.

## Completion Criteria

Phase 6 is complete only when:

- Critical paper UI workflow has browser smoke coverage: complete.
- Paper account summary and paper PnL state are inspectable without broker fields: complete.
- Risk and audit visibility are available from the UI or API: complete.
- Focused paper tests, backend regression, frontend build, and browser smoke pass: complete.
- Safety grep confirms no broker SDK, broker credentials, live order methods, trading-scope MCP tools, or paper-to-live controls were introduced: complete.
- Project docs and Yasin Brain record that live execution remains out of scope: complete.
