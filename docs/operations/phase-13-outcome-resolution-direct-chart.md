# Phase 13 Outcome Resolution Direct Chart Fix

Status: Partial Runtime Verification
Last Reviewed: 2026-06-22
Owner: Yasin

## Purpose

Remove the residual `fc.yahoo.com` outcome-resolution warning that still appeared after Phase 13 Slice 2.

## Problem

Phase 12 moved core market data and technical-indicator OHLCV to `direct_yahoo_chart`, but the deferred reflection outcome resolver still used:

```text
yfinance.Ticker(...).history(...)
```

That path can hit yfinance's cookie/crumb host and emit:

```text
fc.yahoo.com SSL hostname validation
```

## Change

- `TradingAgentsGraph._fetch_returns()` now uses `direct_yahoo_chart._download_chart_frame()` for both the analyzed ticker and the benchmark.
- The method still preserves symbol normalization before fetching the analyzed ticker.
- The method still returns `(None, None, None)` when price data is unavailable or too short.
- The unused `yfinance` import was removed from `tradingagents/graph/trading_graph.py`.

## Verification

Ran in isolated Ubuntu copy:

```text
/tmp/tradingagents-phase13-outcome-fix
```

Focused regression:

```bash
PYTHONPATH=. /home/yasin/workspace/TradingAgents/backend/.venv/bin/python -m pytest \
  tests/test_memory_log.py::TestDeferredReflection::test_fetch_returns_valid_ticker \
  tests/test_memory_log.py::TestDeferredReflection::test_fetch_returns_uses_direct_yahoo_chart_not_yfinance \
  tests/test_memory_log.py::TestDeferredReflection::test_fetch_returns_too_recent \
  tests/test_memory_log.py::TestDeferredReflection::test_fetch_returns_delisted \
  tests/test_memory_log.py::TestDeferredReflection::test_fetch_returns_spy_shorter_than_stock \
  tests/test_symbol_normalization_paths.py \
  tests/test_direct_yahoo_chart.py -q
```

Result:

```text
12 passed
```

Broader deferred-reflection regression:

```bash
PYTHONPATH=. /home/yasin/workspace/TradingAgents/backend/.venv/bin/python -m pytest \
  tests/test_memory_log.py \
  tests/test_symbol_normalization_paths.py \
  tests/test_direct_yahoo_chart.py -q
```

Result:

```text
76 passed
```

## Runtime Check

Attempted a guarded `SPY 2026-06-18` real-runner smoke in the same isolated copy after copying the runtime database and explicitly enabling the real-runner gate. The run produced no `fc.yahoo.com` warning, but it also did not return a final JSON result within the waiting window and was interrupted.

Attempted a smaller live `_fetch_returns()` check with `yfinance.Ticker` patched to fail immediately. That check also waited on external chart requests and was interrupted without output.

These runtime attempts are not counted as passed verification. The verified evidence for this slice is the focused and broader unit regression that proves `_fetch_returns()` no longer uses `yfinance.Ticker`.

## Decision

Do not expand to `QQQ` yet.

Next action:

- Add a bounded non-LLM runtime probe for direct chart outcome-resolution with clearer timeout/output behavior.
- Then repeat the guarded provider-backed SPY review path before reconsidering QQQ.

## Boundary

- No broker integration was added.
- No live execution was added.
- No live-trading UI control was added.
- No scheduled provider-backed research job was added.
- No automatic retry loop was added.
- No paper-to-live workflow was added.
- No secret values were read, printed, copied, or recorded.
