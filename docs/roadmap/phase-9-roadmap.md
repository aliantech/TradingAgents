# Phase 9 Roadmap

## Objective

Phase 9 turns the now-operable research execution path into an evaluable research workflow.

The immediate goal is to make deterministic and manually gated real TradingAgents outputs easier to compare, review, score, and improve without expanding into live trading.

This phase is not a live-trading phase. It does not add broker order placement, broker credentials, broker account mutation, AI-directed live trading, trading-scope MCP tools, live-trading UI controls, scheduled provider-backed research jobs, or automatic paper-to-live promotion.

## Entry State

Phase 8 completed research operations hardening:

- Runner mode settings UX for persisted `AQUANTLENS_TRADINGAGENTS_*` runtime settings.
- Guarded manual real-runner smoke CLI and wrapper.
- Chinese-first report quality contract before persistence.
- Normalized failed-run diagnostics visible in Runs.
- Completion audit: `docs/roadmap/phase-8-completion-audit.md`.

Known post-Phase-8 gaps:

- Real provider-backed TradingAgents research remains manual and has not been product-evaluated across a repeatable symbol/date set.
- Report quality checks validate structure and safety language, not usefulness, evidence quality, consistency, or operator trust.
- There is no compact evaluation record that compares deterministic and real-runner outputs across the same inputs.
- Runs UI shows failures and reports, but not a review workflow for rating report quality or recording operator notes.

## Design Principles

- Evaluation before automation.
- Research quality before trading workflows.
- Keep deterministic mode as the default baseline.
- Keep real provider-backed execution manual, explicit, and reversible.
- Prefer small review artifacts over opaque scoring.
- Never require secrets in automated tests.
- Never read, print, store, or expose secret values in logs, reports, tests, or docs.
- Live broker execution remains out of scope.

## Phase 9 Slices

### Slice 1: Phase 9 Roadmap and Evaluation Boundary

Status: planned.

Goal:

- Define the research evaluation phase and preserve the no-live-trading boundary.

Deliverables:

- Phase 9 roadmap.
- Slice 1 implementation plan.
- Project status update marking Phase 9 as research evaluation and provider pilot planning.
- Yasin Brain log entry recording that real provider research remains manual and live execution remains out of scope.

Verification:

- Documentation points Phase 9 to evaluation, review, and manual provider pilot readiness.
- Documentation keeps broker credentials, broker account mutation, trading-scope MCP tools, live-trading UI controls, scheduled provider-backed research jobs, automatic retry loops, and paper-to-live promotion out of scope.
- No runtime code is added in Slice 1.

### Slice 2: Evaluation Case Set

Status: planned.

Goal:

- Define a small, versioned evaluation case set for repeatable research-output comparison.

Expected coverage:

- Symbols across SPY, QQQ, one mega-cap equity, one volatile equity, and one index-oriented case.
- Fixed analysis dates and research templates.
- Deterministic runner baseline expected outputs or quality expectations.
- No provider secrets and no live provider calls in tests.

Verification:

- Backend tests load and validate the case set.
- Documentation explains how operators should extend cases.

### Slice 3: Report Review Contract

Status: planned.

Goal:

- Add a lightweight review contract for operator assessment of report quality.

Expected coverage:

- Review dimensions: evidence clarity, consistency, risk coverage, options relevance, Chinese readability, and research-only safety.
- Free-text reviewer notes.
- Review storage through existing database boundaries.
- No investment correctness scoring and no automated trading authority.

Verification:

- Backend tests cover creating and listing reviews.
- Existing report APIs still pass.

### Slice 4: Review UI for Reports and Runs

Status: planned.

Goal:

- Add a focused UI flow for reviewing completed reports and failed/no-report runs.

Expected coverage:

- Reports expose review status and latest note.
- Runs detail can show review context next to report/failure diagnostics.
- Retry remains explicit and user-controlled.

Verification:

- Frontend build passes.
- Mocked browser smoke covers adding or viewing a review without provider calls.

### Slice 5: Manual Provider Pilot SOP

Status: planned.

Goal:

- Document and verify a safe operator workflow for manually comparing deterministic and real-runner outputs.

Expected coverage:

- Uses the Phase 8 guarded smoke path.
- Requires explicit runtime gate and operator-provided environment.
- Records only non-secret metadata, output quality notes, and residual risks.
- Does not run in CI or scheduled jobs.

Verification:

- SOP exists and safety grep confirms it does not source `.env`, print secrets, or encourage automated provider calls.
- Tests continue to mock real runner behavior.

### Slice 6: Evaluation Summary and Completion Audit

Status: planned.

Goal:

- Audit Phase 9 and record whether the research workflow is ready for broader manual provider pilots.

Verification:

- Focused evaluation/review tests pass.
- Full backend regression passes.
- Frontend build passes.
- Relevant browser smoke passes.
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
- Automatic retry loops for failed research runs.
- Production-grade distributed job orchestration.
- Public multi-user SaaS execution.

## Completion Criteria

Phase 9 is complete only when:

- A small repeatable research evaluation case set exists.
- Operator review contracts exist for completed reports and relevant failed/no-report runs.
- Reports/Runs UI exposes review context without provider calls in browser tests.
- Manual provider pilot SOP is documented and remains opt-in.
- Focused tests, full backend regression, frontend build, and relevant browser smoke pass.
- Safety grep confirms no live-execution boundary violations.
- Project docs and Yasin Brain record that live execution remains out of scope.
