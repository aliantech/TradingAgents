# Phase 12 Roadmap

## Objective

Phase 12 fixes the Phase 11 real-runner market-data blocker before any expansion beyond `SPY`.

The immediate goal is to replace the failing yfinance cookie/crumb path for core OHLCV data with a minimal direct Yahoo Finance chart endpoint vendor, validate that endpoint independently, then repeat the guarded `SPY` smoke only after the market-data path is verified.

This phase is not a live-trading phase. It does not add broker order placement, broker credentials, broker account mutation, AI-directed live trading, trading-scope MCP tools, live-trading UI controls, scheduled provider-backed research jobs, automatic retry loops, or automatic paper-to-live promotion.

## Entry State

Phase 11 completed with a market-data runtime failure:

- Settings API confirmed the provider key is saved as a write-only secret.
- The guarded smoke CLI can bridge Settings-stored provider keys into the process without printing them.
- The approved `SPY` wrapper reached the real TradingAgents runner.
- The run failed before report generation because Yahoo/yfinance SSL hostname validation hit the `fc.yahoo.com` path.
- The Phase 11 decision was to fix the market-data SSL/runtime path, then repeat `SPY`; do not expand to `QQQ`.

## Design Principles

- Validate the current Yahoo Finance chart endpoint before replacing the data path.
- Keep the fix narrow: core OHLCV `get_stock_data` only.
- Do not route through yfinance for this new core OHLCV path.
- Preserve existing vendor routing and fallback semantics.
- Keep deterministic mode as the default runner.
- Keep real provider-backed research manual and opt-in behind explicit runtime gates.
- Record only sanitized metadata and bounded evidence.

## Phase 12 Slices

### Slice 1: Direct Yahoo Chart Vendor

Status: complete.

Goal:

- Add a minimal direct Yahoo chart endpoint vendor for core OHLCV data.
- Configure the real TradingAgents runner to use that vendor for `get_stock_data`.
- Verify the vendor with focused tests and a bounded live SPY OHLCV check.

Result:

- Added `tradingagents/dataflows/direct_yahoo_chart.py`.
- Added `direct_yahoo_chart` to the TradingAgents vendor router.
- Configured the backend real-runner config to route `get_stock_data` to `direct_yahoo_chart`.
- Confirmed `query1.finance.yahoo.com/v8/finance/chart/SPY` and `query2.finance.yahoo.com/v8/finance/chart/SPY` return usable chart payloads.
- Confirmed the new vendor returns one SPY OHLCV row for `2026-06-18`.
- Evidence record: `docs/operations/phase-12-direct-yahoo-chart-validation.md`.

### Slice 2: Repeat SPY Guarded Smoke

Status: complete.

Goal:

- Repeat the approved guarded `SPY` smoke after the core OHLCV path has been fixed.

Verification:

- Uses only `scripts/phase8_real_runner_smoke.sh`.
- Requires explicit runtime gate and operator environment.
- Does not source `.env`, print secrets, or run in CI/schedulers.
- Records only sanitized progress, evidence labels, report-generated status, quality notes, and residual risks.

Result:

- Guarded `SPY` smoke succeeded after follow-up data-path fixes.
- Report generated: true.
- Evidence labels: `tradingagents-real-runner`.
- Evidence record: `docs/operations/phase-12-spy-real-runner-smoke.md`.

### Slice 3: Provider-Backed SPY Review

Status: pending.

Goal:

- If a provider-backed report is generated, review it with the Phase 9 six-dimension review workflow.

Verification:

- Review covers evidence clarity, consistency, risk coverage, options relevance, Chinese readability, research-only safety, and notes.
- Review compares against the Phase 10 deterministic baseline.
- If no report is generated, record a failure decision instead of inventing a review.

### Slice 4: Expansion Decision

Status: pending.

Goal:

- Decide whether to repeat SPY, fix another blocker, expand to QQQ, or stop.

Verification:

- Decision is based on the actual SPY smoke and review outcome.
- Boundary remains research-only and manual.

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

Phase 12 is complete only when:

- The direct Yahoo chart vendor is verified for bounded OHLCV retrieval.
- The guarded SPY smoke is repeated or a documented blocker prevents it.
- If a provider-backed report is generated, it is reviewed with the Phase 9 review dimensions.
- A decision record states whether to repeat SPY, fix another blocker, expand to QQQ, or stop.
- Safety grep confirms no live-execution or secret-exposure boundary violations.
- Project docs and Yasin Brain record the final decision.
