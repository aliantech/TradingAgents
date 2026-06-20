# Phase 11 Decision Record

Status: Complete
Last Reviewed: 2026-06-20
Owner: Yasin

## Decision

Fix the real-runner market-data SSL/runtime path, then repeat `SPY`.

Do not expand to `QQQ` yet.

## Evidence Reviewed

- Phase 10 deterministic baseline review: `docs/operations/phase-10-spy-deterministic-baseline-review.md`.
- Phase 11 Settings key bridge: `docs/operations/phase-11-settings-key-readiness-bridge.md`.
- Phase 11 repeat-SPY smoke: `docs/operations/phase-11-spy-repeat-real-runner-smoke.md`.

## Rationale

Phase 11 removed the previous provider-readiness blocker:

- Settings API has a write-only `OPENAI_API_KEY` saved.
- The guarded smoke CLI can now use Settings-stored provider keys without printing them.
- The explicit real-runner gate is enabled.
- The approved wrapper reaches the real runner.

The remaining blocker is not provider readiness. The current blocker is the TradingAgents market-data path failing through Yahoo/yfinance SSL hostname validation before a research report is produced.

Because no provider-backed report exists, expanding to `QQQ` would not test the intended report-quality workflow. It would only duplicate the same runtime data failure on another case.

## Next Action

Fix or replace the real-runner market-data dependency path for the guarded smoke, then repeat `SPY`.

Acceptable next approaches:

- Configure the real runner to use an already-approved AQuantLens market-data provider path.
- Patch the TradingAgents data layer to avoid the failing Yahoo/yfinance SSL path for manual smoke.
- Add a narrow SPY fixture/data handoff only if it is explicitly labeled as non-provider-backed and not used to claim real-runner report quality.

## Boundary

- No expansion to `QQQ` until `SPY` produces reviewable provider-backed output or a different explicit decision is recorded.
- No `.env` sourcing or environment dumps.
- No broker integration, live execution, scheduled job, automatic retry, or paper-to-live workflow.
