# Phase 8 Real TradingAgents Runner Smoke

Status: Active
Last Reviewed: 2026-06-20
Owner: Yasin

## Purpose

This is the guarded manual smoke path for provider-backed TradingAgents research execution in the AQuantLens US/options branch.

It is an operator-triggered research check. It is not a scheduled job, not live trading, and not a broker workflow.

## Preconditions

- Runtime setting `AQUANTLENS_TRADINGAGENTS_RUNNER_MODE` is saved as `real-tradingagents`.
- Runtime settings choose the intended provider and models.
- The selected provider's required environment variable is present in the process environment.
- The operator passes the explicit confirmation flag through the wrapper script.

The command does not read `.env`, does not print environment variables, and does not print secret values.

## Command

From the repository root:

```bash
scripts/phase8_real_runner_smoke.sh SPY 2026-06-20 etf
```

The wrapper delegates to:

```bash
cd backend
python -m app.analysis.cli real-runner-smoke \
  --symbol SPY \
  --analysis-date 2026-06-20 \
  --asset-type etf \
  --i-understand-this-calls-a-real-llm-provider
```

## Output

The command prints one JSON object with:

- `status`: `succeeded`, `not_ready`, or `failed`.
- `missing`: missing readiness gates, such as the explicit confirmation flag, runner mode, or provider environment variable name.
- `progress`: sanitized runner progress or sanitized failure message.
- `report_generated`: whether a report payload was produced by the runner.
- `evidence_labels`: report evidence labels when the runner succeeds.

Failure text is redacted through the existing TradingAgents adapter error sanitizer.

## Safety Boundary

- Do not add this smoke to CI, background jobs, schedulers, or browser tests.
- Do not source `.env` in this script.
- Do not print secret values, token values, full environment dumps, or provider request payloads.
- Do not add broker SDKs, broker credentials, broker account mutation, order placement, live-trading UI controls, trading-scope MCP tools, or automatic paper-to-live promotion.
