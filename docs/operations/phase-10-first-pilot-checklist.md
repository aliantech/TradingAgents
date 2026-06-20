# Phase 10 First Manual Provider Pilot Checklist

Status: Active
Last Reviewed: 2026-06-20
Owner: Yasin

## Purpose

This checklist controls the first Phase 10 manual provider pilot.

The first pilot compares deterministic baseline output and guarded real TradingAgents runner output for `SPY`.

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

The first pilot is successful only if:

- A deterministic baseline report is available and reviewed.
- The real-runner smoke uses only the Phase 8 guarded wrapper.
- The real-runner output or not-ready result is captured as sanitized non-secret metadata.
- Operator notes compare evidence clarity, consistency, risk coverage, options relevance, Chinese readability, and research-only safety.
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
2. Confirm Phase 9 completion audit exists.
3. Generate or identify the deterministic `SPY` baseline report.
4. Add a report review in the Reports workbench.
5. Confirm runtime settings are intentionally set for manual real-runner mode.
6. Run only the guarded wrapper:

```bash
scripts/phase8_real_runner_smoke.sh SPY 2026-06-18 etf
```

7. Record only non-secret metadata:
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
8. Decide one outcome:
   - Repeat `SPY`.
   - Expand to `QQQ`.
   - Pause for report quality fixes.
   - Stop the manual pilot.

## Recording Rules

Allowed:

- Provider name.
- Model names.
- Case id and symbol.
- Sanitized progress status.
- Evidence labels.
- Review scores and notes.
- Residual risk descriptions.

Forbidden:

- Secret values.
- Provider request payloads.
- Raw provider response dumps.
- Full environment dumps.
- Browser sessions.
- Broker credentials.
- Account identifiers.
- Order identifiers.
