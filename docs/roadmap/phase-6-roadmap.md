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

Status: planned.

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

Status: planned.

Goal:

- Add a minimal browser smoke path for Strategy Lab Candidate-to-Paper UI.

Expected coverage:

- Open Strategy Lab.
- Locate Candidate Review Board paper action.
- Confirm paper-only UI copy and absence of live-trading controls.
- Exercise the review panel against controlled API fixtures or test-backed app state.

Verification:

- Ubuntu browser or Playwright verification runs successfully.
- Frontend build still passes.
- Safety grep confirms no live-trading UI copy.

### Slice 3: Paper Account and Position Summary API

Status: planned.

Goal:

- Add a compact paper account summary endpoint for UI and operator inspection.

Expected coverage:

- Cash.
- Positions.
- Open or recently handled intents.
- Recent fills.
- Recent audit events.

Verification:

- Backend tests prove summary data is account-scoped.
- Backend tests prove no broker account fields or live order fields are exposed.
- Existing paper API tests continue passing.

### Slice 4: Paper PnL Snapshot

Status: planned.

Goal:

- Add paper-only unrealized/realized PnL snapshot logic using explicit caller-provided or stored reference prices.

Expected coverage:

- Equity/ETF position market value.
- Option position market value using paper reference price, not broker quote.
- Cash plus position value account equity.
- Clear stale-price or missing-price state.

Verification:

- Pure calculation tests cover long/short-like position states that are allowed by current paper contracts.
- API tests prove PnL output does not include broker account or live execution fields.
- No external market-data fetch is introduced inside paper PnL calculation.

### Slice 5: Paper Risk Dashboard UI

Status: planned.

Goal:

- Add a compact Strategy Lab or paper panel view for paper account exposure and recent paper workflow state.

Expected coverage:

- Cash and estimated paper equity.
- Position table.
- Recent paper intents and outcomes.
- RiskGuard rejection reason visibility.
- Audit trail preview.

Verification:

- Frontend build passes.
- Browser smoke covers key visible states.
- UI copy remains paper-only.

### Slice 6: Phase 6 Completion Audit

Status: planned.

Goal:

- Audit Phase 6 after slices are implemented and record residual risks.

Verification:

- Focused backend paper tests pass.
- Full backend regression passes.
- Frontend build passes.
- Browser smoke passes.
- Safety grep only matches negative tests or explicit non-goal docs.
- Project docs and Yasin Brain record completion and remaining live-execution boundary.

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

- Critical paper UI workflow has browser smoke coverage.
- Paper account summary and paper PnL state are inspectable without broker fields.
- Risk and audit visibility are available from the UI or API.
- Focused paper tests, backend regression, frontend build, and browser smoke pass.
- Safety grep confirms no broker SDK, broker credentials, live order methods, trading-scope MCP tools, or paper-to-live controls were introduced.
- Project docs and Yasin Brain record that live execution remains out of scope.
