# Phase 9 Manual Provider Pilot SOP

Status: Active
Last Reviewed: 2026-06-20
Owner: Yasin

## Purpose

This SOP defines the manual provider pilot workflow for comparing deterministic AQuantLens research outputs with explicitly gated real TradingAgents runner outputs.

The pilot is for research quality evaluation only. It is not live trading, not paper-to-live promotion, not a broker workflow, not a scheduler workflow, and not a CI workflow.

## Preconditions

- Phase 9 evaluation cases exist in `backend/app/research_evaluation/cases.py`.
- Report review APIs and UI are available for recording operator quality notes.
- The operator has already configured runtime settings through the app settings path.
- Runtime setting `AQUANTLENS_TRADINGAGENTS_RUNNER_MODE` is explicitly set to `real-tradingagents`.
- Runtime settings choose the intended provider and models.
- The selected provider's required environment variable is present in the operator process environment.
- The operator understands that the guarded smoke path may call a real LLM provider.

Do not read, print, copy, paste, summarize, or commit secret values.

## Approved Manual Path

Use the Phase 8 guarded wrapper only:

```bash
scripts/phase8_real_runner_smoke.sh SPY 2026-06-20 etf
```

The wrapper delegates to the guarded backend CLI and requires the explicit confirmation flag already built into the wrapper.

Do not add this command to CI, cron, systemd timers, background workers, browser tests, or scheduled jobs.

## Pilot Case Selection

Start with one or two Phase 9 cases, not the full set:

- `SPY`: broad U.S. equity ETF macro/options read-through.
- `QQQ`: growth-heavy ETF technical setup.

Expand to `AAPL`, `TSLA`, and `SPX` only after the first two cases produce useful, reviewable output and no secret-handling or runtime-boundary issue appears.

## Operator Steps

1. Run the deterministic baseline through the normal Analysis UI or API for the chosen case.
2. Open the completed report in Reports.
3. Add a report review covering evidence clarity, consistency, risk coverage, options relevance, Chinese readability, research-only safety, and notes.
4. Run the guarded manual real-runner smoke for the same symbol, date, and asset type.
5. Record only non-secret pilot metadata:
   - Case id.
   - Symbol.
   - Analysis date.
   - Asset type.
   - Runner mode.
   - Provider name.
   - Quick/deep model names.
   - Whether a report was generated.
   - Sanitized progress status.
   - Evidence labels.
   - Operator quality notes.
   - Residual risks.
6. Do not record provider request payloads, response raw dumps, secret values, token values, browser sessions, or environment dumps.
7. If the real-runner output is persisted through a later manual path, review it with the same report review dimensions before comparing it against the deterministic baseline.

## Stop Conditions

Stop the pilot immediately if any of these occur:

- A command would require reading or printing secret values.
- A command attempts to source `.env` or dump environment variables.
- A script tries to run outside the explicit guarded smoke path.
- A run attempts broker access, order placement, account mutation, or live-trading UI behavior.
- A run is added to CI, a scheduler, a background worker, or an automatic retry loop.
- Provider output contains content that cannot pass the research-only report quality boundary.

## Comparison Notes

Use human review notes instead of opaque scores as the primary decision artifact.

Minimum notes:

- What improved versus deterministic output.
- What became worse or less trustworthy.
- Whether evidence labels are clearer.
- Whether options observations are useful.
- Whether Chinese readability is operator-ready.
- Whether research-only safety language remains clear.
- Whether the pilot should be repeated, expanded, or paused.

## Safety Boundary

- No live broker order placement.
- No broker credential storage or mutation.
- No broker account balance or order-status sync.
- No AI-directed live trading authority.
- No trading-scope MCP tools.
- No live-trading UI controls.
- No automatic paper-to-live promotion.
- No scheduled provider-backed research jobs.
- No automatic retry loops.
- No provider calls in automated tests.
