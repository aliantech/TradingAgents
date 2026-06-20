# Phase 11 Roadmap

## Objective

Phase 11 repeats the SPY manual provider pilot after provider readiness is confirmed without exposing secret values.

The immediate goal is to produce one reviewable provider-backed SPY research output through the existing guarded real-runner wrapper, then compare it against the Phase 10 deterministic baseline before deciding whether to repeat, fix quality issues, or expand to QQQ.

This phase is not an automation phase and not a live-trading phase. It does not add broker order placement, broker credentials, broker account mutation, AI-directed live trading, trading-scope MCP tools, live-trading UI controls, scheduled provider-backed research jobs, automatic retry loops, or automatic paper-to-live promotion.

## Entry State

Phase 10 completed with a pause decision:

- SPY deterministic baseline review exists: `docs/operations/phase-10-spy-deterministic-baseline-review.md`.
- Guarded SPY real-runner smoke produced a sanitized `not_ready` result: `docs/operations/phase-10-spy-real-runner-smoke.md`.
- First case decision: pause for provider readiness, then repeat `SPY`.
- Completion audit: `docs/roadmap/phase-10-completion-audit.md`.

Known post-Phase-10 gaps:

- No provider-backed SPY report has been generated.
- Real-runner output quality, evidence labels, Chinese readability, and options relevance remain unreviewed.
- QQQ expansion is not authorized until SPY produces reviewable real-runner output or a new explicit decision is recorded.

## Design Principles

- Confirm readiness without printing, copying, storing, or committing secret values.
- Use only `scripts/phase8_real_runner_smoke.sh` for real-runner execution.
- Repeat `SPY` before considering `QQQ`.
- Record sanitized metadata only.
- Treat provider output as research-only material, not trading authority.
- Stop on any secret exposure, wrapper bypass, broker access, scheduler, automatic retry, or live-execution signal.

## Phase 11 Slices

### Slice 1: Roadmap and Repeat-SPY Checklist

Status: complete.

Goal:

- Define the Phase 11 repeat-SPY process, readiness boundary, success criteria, and stop criteria.

Deliverables:

- Phase 11 roadmap.
- Repeat-SPY provider readiness checklist.
- Project status update marking Phase 11 as underway.
- Yasin Brain log entry recording the provider-readiness-only boundary.

Verification:

- Documentation keeps provider-backed research manual and opt-in.
- Documentation keeps secret values, `.env` sourcing, broker workflows, scheduled jobs, automatic retries, live execution, and paper-to-live promotion out of scope.
- No runtime code is added in Slice 1.

### Slice 2: Provider Readiness Check

Status: complete.

Goal:

- Confirm the operator process that will run the approved wrapper has the required provider environment variable available without exposing its value.

Verification:

- Readiness is recorded as `ready` or `not_ready`.
- Only variable names and boolean readiness are recorded.
- No secret value, `.env` content, environment dump, provider request payload, or provider raw response is recorded.
- No wrapper run occurs if readiness is not confirmed.

Result:

- Readiness result: `not_ready`.
- Missing readiness gate: `OPENAI_API_KEY`.
- Evidence record: `docs/operations/phase-11-provider-readiness-check.md`.
- The approved wrapper was not executed because readiness was not confirmed.

### Slice 3: Repeat SPY Guarded Real-Runner Smoke

Status: waiting on provider readiness.

Goal:

- Run the approved wrapper for `SPY` with the same first-case inputs after readiness is confirmed.

Approved command:

```bash
scripts/phase8_real_runner_smoke.sh SPY 2026-06-18 etf
```

Verification:

- Uses only `scripts/phase8_real_runner_smoke.sh`.
- Requires explicit runtime gate and operator environment.
- Does not source `.env`, print secrets, or run in CI/schedulers.
- Captures only sanitized progress, evidence labels, report-generated status, quality notes, and residual risks.

### Slice 4: Provider-Backed SPY Review

Status: planned.

Goal:

- If a provider-backed report is generated, review it with the Phase 9 six-dimension review workflow.

Verification:

- Review covers evidence clarity, consistency, risk coverage, options relevance, Chinese readability, research-only safety, and notes.
- Review compares against the Phase 10 deterministic baseline.
- If no report is generated, record a failure/not-ready decision instead of inventing a review.

### Slice 5: Expansion Decision

Status: planned.

Goal:

- Decide whether to repeat SPY, fix quality issues, expand to QQQ, or stop.

Verification:

- Decision record compares deterministic and provider-backed SPY evidence.
- Decision is one of: repeat SPY, fix quality issues, expand to QQQ, or stop.
- Boundary remains research-only and manual.

### Slice 6: Completion Audit

Status: planned.

Goal:

- Audit Phase 11 and record whether QQQ expansion is justified.

Verification:

- Relevant focused backend tests pass.
- Frontend build and report review browser smoke pass if UI changed.
- Safety grep confirms no secret, live-execution, scheduler, automatic retry, broker, or paper-to-live boundary violations.
- Project docs and Yasin Brain record completion and residual risks.

## Explicit Non-Goals

- QQQ execution before SPY produces reviewable provider-backed output or a new explicit decision.
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

Phase 11 is complete only when:

- Provider readiness for the approved wrapper process is recorded without exposing secret values.
- SPY guarded real-runner smoke either generates a provider-backed report or produces a documented not-ready/failure result.
- If a report is generated, it is reviewed with the Phase 9 review dimensions.
- A decision record states whether to repeat SPY, fix quality issues, expand to QQQ, or stop.
- Safety grep confirms no live-execution or secret-exposure boundary violations.
- Project docs and Yasin Brain record the final decision.
