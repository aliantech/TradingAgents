# Phase 12 SPY Real-Runner Smoke

Status: Complete
Last Reviewed: 2026-06-20
Owner: Yasin

## Purpose

Repeat the guarded `SPY` real-runner smoke after fixing the Phase 11 Yahoo/yfinance market-data blocker.

This smoke verifies whether the real TradingAgents runner can produce one provider-backed SPY research output through the existing guarded wrapper.

## Approved Command

```bash
scripts/phase8_real_runner_smoke.sh SPY 2026-06-18 etf
```

Runtime gate:

```text
AQUANTLENS_TRADINGAGENTS_RUNNER_MODE=real-tradingagents
```

## Attempts

### Attempt 1

Result:

```text
failed
```

Failure:

```text
No market data for 'SPY': Yahoo Finance returned no rows
```

Interpretation:

- Core `get_stock_data` had been moved to `direct_yahoo_chart`.
- Technical indicator OHLCV still used `stockstats_utils.load_ohlcv -> yf.download`, which triggered the same yfinance `fc.yahoo.com` SSL path.

Action:

- Added direct Yahoo chart support for technical indicator OHLCV.
- Configured real-runner `get_indicators` to use `direct_yahoo_chart`.

### Attempt 2

Result:

```text
failed
```

Failure:

```text
FRED_API_KEY environment variable is not set.
```

Interpretation:

- The Yahoo/yfinance data blocker was cleared.
- The next blocker was required FRED macro data configuration.

Action:

- Added explicit `macro_unavailable` vendor for manual research smoke.
- Configured real-runner `get_macro_indicators` to return a visible `NO_DATA_AVAILABLE` macro signal instead of aborting the whole run.

### Attempt 3

Result:

```text
succeeded
```

Sanitized result:

```json
{
  "symbol": "SPY",
  "status": "succeeded",
  "runner_mode": "real-tradingagents",
  "llm_provider": "openai",
  "model": "gpt-5.5",
  "missing": [],
  "report_generated": true,
  "evidence_labels": ["tradingagents-real-runner"],
  "error_message": null
}
```

Progress:

```text
queued: completed
tradingagents: completed
report: completed
```

## Verification

Ubuntu temp copy:

```text
/tmp/tradingagents-phase12-direct-yahoo-NwLyFG
```

Focused tests after follow-up fixes:

```text
tests/test_direct_yahoo_chart.py
tests/test_fred.py
tests/test_vendor_routing.py
tests/test_dataflows_config.py
```

Result:

```text
28 passed
```

Backend runner config tests:

```text
backend/tests/test_tradingagents_runner.py
```

Result:

```text
6 passed
```

## Decision

Proceed to Phase 12 provider-backed SPY report review using the Phase 9 review dimensions.

Do not expand to `QQQ` until the SPY report is reviewed.

## Boundary

- No broker integration was added.
- No live execution was added.
- No live-trading UI control was added.
- No scheduled provider-backed research job was added.
- No automatic retry loop was added.
- No paper-to-live workflow was added.
- No secret values were read, printed, copied, or recorded.
