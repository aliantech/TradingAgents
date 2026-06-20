# Phase 11 Repeat-SPY Provider Readiness Checklist

Status: Active
Last Reviewed: 2026-06-20
Owner: Yasin

## Purpose

This checklist controls the Phase 11 repeat-SPY provider readiness and guarded smoke attempt.

The goal is to repeat `SPY` after provider readiness is confirmed, using only the existing guarded wrapper.

This checklist does not authorize live trading, broker access, scheduled provider jobs, automatic retries, or paper-to-live promotion.

## Case

- Case id: `spy-macro-options-2026-06-18`.
- Symbol: `SPY`.
- Asset type: `etf`.
- Analysis date: `2026-06-18`.
- Research template: `macro-options-readthrough`.
- Analyst set: `macro-options`.
- Language: `zh`.

## Success Criteria

The repeat-SPY attempt is successful only if:

- Provider readiness is confirmed without exposing secret values.
- The real-runner smoke uses only the Phase 8 guarded wrapper.
- The real-runner output or not-ready/failure result is captured as sanitized non-secret metadata.
- If a report is generated, operator notes review evidence clarity, consistency, risk coverage, options relevance, Chinese readability, and research-only safety.
- No secret value is read, printed, copied, pasted, stored, or committed.
- No broker, live execution, scheduled job, automatic retry, or paper-to-live behavior appears.

## Stop Criteria

Stop immediately if:

- Any command requires reading or printing secret values.
- Any command attempts to source `.env` or dump environment variables.
- Any path bypasses `scripts/phase8_real_runner_smoke.sh`.
- Any run attempts broker access, order placement, account mutation, or live-trading UI behavior.
- Any run is added to CI, a scheduler, a background worker, or an automatic retry loop.
- Output cannot pass the research-only report quality boundary.

## Manual Steps

1. Confirm the worktree is clean.
2. Confirm Phase 10 completion audit exists.
3. Confirm the deterministic `SPY` baseline review exists.
4. Confirm the Phase 10 decision requires repeating `SPY`, not expanding to `QQQ`.
5. Confirm runtime settings are intentionally set for manual real-runner mode.
6. Confirm the required provider environment variable is available to the wrapper process without printing or copying its value.
7. Run only the guarded wrapper:

```bash
scripts/phase8_real_runner_smoke.sh SPY 2026-06-18 etf
```

8. Record only non-secret metadata:
   - Case id.
   - Symbol.
   - Analysis date.
   - Asset type.
   - Runner mode.
   - Provider name.
   - Quick/deep model names.
   - Status.
   - Missing readiness gates if any.
   - Sanitized progress status.
   - Whether a report was generated.
   - Evidence labels.
   - Operator notes.
   - Residual risks.
9. If a report is generated, review it with the Phase 9 review dimensions.
10. Decide one outcome:
    - Repeat `SPY`.
    - Fix report quality issues.
    - Expand to `QQQ`.
    - Stop the manual pilot.

## Recording Rules

Allowed:

- Provider name.
- Model names.
- Required environment variable names.
- Boolean readiness state.
- Case id and symbol.
- Sanitized progress status.
- Evidence labels.
- Review scores and notes.
- Residual risk descriptions.

Forbidden:

- Secret values.
- `.env` contents.
- Full environment dumps.
- Provider request payloads.
- Raw provider response dumps.
- Browser sessions.
- Broker credentials.
- Account identifiers.
- Order identifiers.
