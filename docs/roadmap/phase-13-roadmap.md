# Phase 13 Roadmap

## Objective

Phase 13 fixes the Phase 12 SPY provider-backed report data-grounding failure before any expansion to `QQQ`.

The immediate goal is to make real-runner report persistence reject market/technical price claims that conflict with the deterministic direct Yahoo chart snapshot. A provider-backed report with unsupported or conflicting exact close claims should fail the report-quality path instead of being saved as a completed research report.

This phase is not a live-trading phase. It does not add broker order placement, broker credentials, broker account mutation, AI-directed live trading, trading-scope MCP tools, live-trading UI controls, scheduled provider-backed research jobs, automatic retry loops, or automatic paper-to-live promotion.

## Entry State

Phase 12 completed with a fix-before-expansion decision:

- The guarded `SPY` real-runner smoke generated and persisted a provider-backed report.
- The Phase 9-style review failed expansion readiness.
- Primary blocker: the report stated `SPY` close `746.74` for `2026-06-18`, while the direct Yahoo chart validation returned `549.33` for the same date.
- Decision: do not expand to `QQQ`; fix SPY report data-grounding first.

## Slice 1: Real-Runner Data-Grounding Gate

Status: complete.

Goal:

- Include the deterministic verified market-data snapshot in real-runner mapped reports.
- Add a `direct-yahoo-chart-verified-snapshot` evidence label to real-runner reports.
- Reject real-runner reports when same-date close claims conflict with the verified snapshot close.

Result:

- Real-runner report mapping now includes the verified snapshot in `market_background`, `technical_analysis`, and report markdown.
- Report quality validation now requires real-runner reports to carry a verified snapshot label and markdown snapshot.
- Report quality validation detects same-date close conflicts in market/technical text before persistence.
- Evidence record: `docs/operations/phase-13-spy-data-grounding-gate.md`.

### Slice 2: Repeat SPY Provider Review

Status: complete.

Goal:

- Repeat the provider-backed `SPY` persisted analysis after the data-grounding gate.
- Review the completed report if it persists successfully.
- Decide whether to expand to `QQQ`, repeat SPY, or fix another blocker.

Result:

- Provider-backed `SPY` persisted run completed in an isolated Ubuntu copy.
- Evidence labels included `tradingagents-real-runner` and `direct-yahoo-chart-verified-snapshot`.
- The verified snapshot and current direct Yahoo chart endpoint both returned `SPY` close `746.74` for `2026-06-18`.
- No same-date close conflict was detected.
- Review improved evidence clarity and consistency, but did not approve `QQQ` expansion because options relevance remains placeholder-level, the final mapped trade plan is only `Hold`, and the residual yfinance outcome-resolution warning still appears.
- Evidence record: `docs/operations/phase-13-spy-repeat-provider-review.md`.

### Slice 3: Outcome Resolution Direct Chart Fix

Status: complete for unit regression; runtime verification remains partial.

Goal:

- Remove the remaining `yfinance.Ticker(...).history(...)` path from deferred reflection outcome resolution.
- Preserve realized raw/alpha return behavior.
- Verify that `_fetch_returns()` no longer calls yfinance.

Result:

- `TradingAgentsGraph._fetch_returns()` now uses the direct Yahoo chart frame downloader for both ticker and benchmark prices.
- The yfinance import was removed from `tradingagents/graph/trading_graph.py`.
- Focused outcome-resolution and direct-chart tests passed.
- Broader deferred-reflection regression passed.
- A guarded real-runner smoke produced no `fc.yahoo.com` warning, but did not return final JSON before interruption, so runtime verification is recorded as partial rather than passed.
- Evidence record: `docs/operations/phase-13-outcome-resolution-direct-chart.md`.

### Slice 4: Bounded Outcome Runtime Probe

Status: complete.

Goal:

- Add a non-LLM runtime probe for outcome-resolution.
- Make the probe bounded with explicit timeout and JSON output.
- Fail visibly if `yfinance.Ticker` is reached.

Result:

- Added `scripts/phase13_outcome_resolution_probe.py`.
- Probe unit tests passed.
- Related deferred-reflection/direct-chart regressions passed.
- Runtime probe for `SPY 2026-06-18` returned `status=succeeded`, `yfinance_ticker_blocked=true`, and no `fc.yahoo.com` warning.
- Evidence record: `docs/operations/phase-13-outcome-resolution-runtime-probe.md`.

### Slice 5: Full SPY Provider Review Rerun

Status: complete.

Goal:

- Repeat the full guarded `SPY` real-runner path after the bounded outcome probe.
- Confirm the old `fc.yahoo.com` warning no longer appears in full real-runner smoke.
- Persist and review a provider-backed `SPY` report.

Result:

- Bounded outcome probe succeeded for `SPY 2026-06-18`.
- Guarded real-runner smoke exited `0`, generated a report, emitted no stderr, and had `fc.yahoo.com` count `0`.
- Persisted provider-backed `SPY` report completed.
- Data-grounding check found no same-date close conflict.
- Review did not approve `QQQ` expansion because options observation remains placeholder-level and the mapped trade plan is still a one-word final decision wrapped in research-only language.
- Evidence record: `docs/operations/phase-13-full-spy-provider-review.md`.

### Slice 6: Real-Runner Report Mapping Improvement

Status: complete for mapping/unit regression; provider-backed persisted review remains pending.

Goal:

- Expand one-word real-runner final decisions into a research-only plan with observation conditions, invalidation conditions, and risk boundaries.
- Replace placeholder options observation text with a concrete options-risk framework.
- Preserve the research-only boundary and avoid adding broker execution, live trading, scheduled jobs, or automatic retry behavior.

Result:

- Real-runner mapped `trade_plan` now includes the original TradingAgents conclusion plus observation conditions, invalidation conditions, risk boundaries, and follow-up review needs.
- Real-runner mapped `options_observation` now names IV, put/call skew, open interest, volume concentration, Gamma exposure, event volatility risk, and the current limitation that no per-contract option chain is returned by the runner.
- Focused mapping, full real-runner mapping, report-quality, and CLI smoke-boundary tests passed in an isolated Ubuntu copy.
- Evidence record: `docs/operations/phase-13-report-mapping-improvement.md`.

### Slice 7: SPY Mapping Provider Review

Status: complete.

Goal:

- Repeat the guarded provider-backed `SPY` smoke after the mapping improvement.
- Persist a new provider-backed `SPY` report in an isolated Ubuntu database.
- Create a fresh review against the improved mapped report.

Result:

- Bounded outcome probe succeeded with `yfinance_ticker_blocked=true`.
- Guarded real-runner smoke exited `0`, generated a report, emitted no stderr, and had `fc.yahoo.com` count `0`.
- Persisted provider-backed `SPY` report completed with evidence labels `tradingagents-real-runner` and `direct-yahoo-chart-verified-snapshot`.
- The old one-word trade-plan wrapper and old options placeholder were absent.
- Review scores improved risk coverage to `4` and options relevance to `3`.
- Remaining blocker: the real runner still does not return per-contract option-chain context, so options relevance is improved but not contract-level.
- Evidence record: `docs/operations/phase-13-spy-mapping-provider-review.md`.

### Slice 8: Option Chain Context

Status: complete for code and unit-contract validation; provider-backed verification remains pending.

Goal:

- Feed persisted option-chain snapshots into real-runner report mapping.
- Include contract-level options context in `options_observation` when available.
- Keep no-data states explicit instead of fabricating options evidence.

Result:

- Added an option-chain context builder that reads the nearest persisted expiry on or after the analysis date.
- `start_analysis()` now passes option-chain context into the TradingAgents execution request when a repository session is available.
- Real-runner `options_observation` includes the persisted context when available and states when no per-contract snapshot exists.
- Tests passed for the context builder, service integration, runner mapping, options repository/API, report quality, and smoke-boundary contracts.
- Runtime DB check found `QQQ` has persisted option-chain snapshots for `2026-06-26`; `SPY` currently has none.
- Evidence record: `docs/operations/phase-13-option-chain-context.md`.

### Slice 9: Option Chain Readiness Gate

Status: complete.

Goal:

- Add an explicit guarded-smoke gate that blocks provider-backed pilots when per-contract option-chain context is required but missing.
- Keep the default smoke behavior unchanged.
- Prevent avoidable provider calls for symbols without required option-chain context.

Result:

- `app.analysis.cli real-runner-smoke` now supports `--require-option-chain-context`.
- `scripts/phase8_real_runner_smoke.sh` now supports optional fourth argument `require-option-chain-context`.
- With the gate enabled, `SPY` returned `not_ready` before runner/provider execution because no persisted SPY option-chain context exists.
- Runtime DB context check from the isolated backend directory found `SPY_CONTEXT False` and `QQQ_CONTEXT True`.
- Evidence record: `docs/operations/phase-13-option-chain-readiness-gate.md`.

## Next Action

`QQQ` is ready for a guarded provider-backed pilot from the readiness-gate perspective: the no-provider preflight returned `not_ready` only because the explicit real-provider confirmation flag was intentionally omitted, and did not report missing persisted option-chain context.

`SPY` was rechecked from the clean mirror and now has the same no-provider preflight shape: `not_ready` only because the explicit real-provider confirmation flag was intentionally omitted.

The actual provider-backed `QQQ` smoke remains pending because the current execution environment blocked sending runtime context and research input to an external LLM/provider. Evidence records: `docs/operations/phase-13-qqq-gated-preflight.md` and `docs/roadmap/phase-13-validation-audit.md`.

Next action is an operator decision outside this restricted execution context:

- run the guarded `QQQ` pilot manually in an approved environment with `require-option-chain-context`; or
- run one guarded repeat `SPY` pilot manually in an approved environment with `require-option-chain-context`.

Do not proceed to additional symbols or retries automatically from the preflight result.

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
