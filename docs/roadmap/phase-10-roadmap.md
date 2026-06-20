# Phase 10 Roadmap

## Objective

Phase 10 runs a narrow manual provider pilot for the AQuantLens US/options research workflow.

The immediate goal is to compare deterministic baseline reports against explicitly gated real TradingAgents runner output for one or two high-priority cases, then decide whether the real-runner path is ready for broader manual pilots.

This phase is not an automation phase and not a live-trading phase. It does not add broker order placement, broker credentials, broker account mutation, AI-directed live trading, trading-scope MCP tools, live-trading UI controls, scheduled provider-backed research jobs, automatic retry loops, or automatic paper-to-live promotion.

## Entry State

Phase 9 completed research evaluation foundations:

- Versioned evaluation cases for SPY, QQQ, AAPL, TSLA, and SPX.
- Report review persistence and APIs.
- Reports/Runs review UI.
- Manual provider pilot SOP.
- Completion audit: `docs/roadmap/phase-9-completion-audit.md`.

Known post-Phase-9 gaps:

- No real provider-backed output has been reviewed against deterministic baseline output through the Phase 9 review workflow.
- There is no pilot decision record showing whether broader manual provider pilots should proceed.
- Real-runner output quality, Chinese readability, evidence labels, and options relevance still need operator assessment.

## Design Principles

- Manual first.
- One or two cases before expansion.
- Deterministic baseline before real-runner comparison.
- Record non-secret metadata only.
- Prefer operator notes over opaque scores.
- Stop on any secret, broker, scheduling, or live-execution boundary issue.
- Keep real provider-backed execution opt-in behind explicit runtime gates.

## Phase 10 Slices

### Slice 1: Roadmap and First Pilot Checklist

Status: complete.

Goal:

- Define Phase 10 scope, success criteria, stop criteria, and the first manual pilot checklist.

Deliverables:

- Phase 10 roadmap.
- First manual provider pilot checklist.
- Project status update marking Phase 10 as manual provider pilot planning.
- Yasin Brain log entry recording the manual-only boundary.

Verification:

- Documentation keeps provider-backed research manual and opt-in.
- Documentation keeps secrets, broker workflows, scheduled jobs, automatic retries, live execution, and paper-to-live promotion out of scope.
- No runtime code is added in Slice 1.

### Slice 2: Deterministic Baseline Review

Status: complete.

Goal:

- Run or identify deterministic baseline output for the first case and record a report review.

Expected first case:

- `SPY` macro/options read-through.

Deliverables:

- SPY deterministic baseline review record in `docs/operations/phase-10-spy-deterministic-baseline-review.md`.
- Slice 2 implementation plan.

Verification:

- Completed deterministic report exists.
- Report review exists with evidence clarity, consistency, risk coverage, options relevance, Chinese readability, research-only safety, and notes.
- No real provider call is made in this slice unless explicitly promoted to Slice 3.

### Slice 3: Guarded Real-Runner Smoke for First Case

Status: planned.

Goal:

- Execute the guarded real-runner smoke manually for the same first case, then capture sanitized non-secret metadata.

Verification:

- Uses only `scripts/phase8_real_runner_smoke.sh`.
- Requires explicit runtime gate and operator environment.
- Does not source `.env`, print secrets, or run in CI/schedulers.
- Captures only sanitized progress, evidence labels, report-generated status, quality notes, and residual risks.

### Slice 4: First Case Decision Record

Status: planned.

Goal:

- Decide whether to repeat, expand, or pause the manual provider pilot.

Verification:

- Decision record compares deterministic and real-runner outputs.
- Decision is one of: repeat same case, expand to QQQ, pause for quality fixes, or stop.
- Boundary remains research-only and manual.

### Slice 5: Optional Second Case Pilot

Status: planned.

Goal:

- If Slice 4 allows expansion, repeat the pilot for QQQ.

Verification:

- Same deterministic baseline, guarded real-runner, review, and decision process is followed.
- No automation or live-execution scope is added.

### Slice 6: Completion Audit

Status: planned.

Goal:

- Audit Phase 10 and record whether broader manual provider pilots are justified.

Verification:

- Relevant focused backend tests pass.
- Frontend build and report review browser smoke pass if UI changed.
- Safety grep confirms no secret, live-execution, scheduler, automatic retry, broker, or paper-to-live boundary violations.
- Project docs and Yasin Brain record completion and residual risks.

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
- Bulk real-runner batch evaluation.
- Public multi-user SaaS execution.

## Completion Criteria

Phase 10 is complete only when:

- At least one deterministic baseline report has a review.
- At least one guarded manual real-runner pilot has either completed or produced a documented not-ready/failure result.
- Non-secret pilot metadata and operator notes are recorded.
- A decision record states whether to repeat, expand, pause, or stop.
- Safety grep confirms no live-execution boundary violations.
- Project docs and Yasin Brain record the final decision.
