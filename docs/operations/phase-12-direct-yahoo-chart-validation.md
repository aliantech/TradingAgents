# Phase 12 Direct Yahoo Chart Validation

Status: Complete
Last Reviewed: 2026-06-20
Owner: Yasin

## Purpose

Phase 11 failed before report generation because the real TradingAgents market-data path hit a Yahoo/yfinance SSL hostname validation failure through `fc.yahoo.com`.

Before changing providers or expanding to `QQQ`, Phase 12 Slice 1 validated the current Yahoo Finance chart endpoint directly and added a narrow core OHLCV vendor that avoids yfinance's cookie/crumb path.

## Endpoint Validation

Validated hosts:

- `query1.finance.yahoo.com`
- `query2.finance.yahoo.com`

Validated endpoint shape:

```text
https://query1.finance.yahoo.com/v8/finance/chart/SPY
https://query2.finance.yahoo.com/v8/finance/chart/SPY
```

Validation result:

- `query1.finance.yahoo.com`: usable SPY chart payload returned.
- `query2.finance.yahoo.com`: usable SPY chart payload returned.
- Both returned one bounded daily OHLCV row for the requested SPY window.

## Implementation

Added:

- `tradingagents/dataflows/direct_yahoo_chart.py`
- `direct_yahoo_chart` vendor registration in `tradingagents/dataflows/interface.py`
- real-runner config override in `backend/app/analysis/tradingagents_runner.py`

Runtime routing change:

- `get_stock_data` now routes to `direct_yahoo_chart` for real TradingAgents runner config.

Scope intentionally left unchanged:

- Technical indicators remain on existing configured vendors.
- Fundamentals remain on existing configured vendors.
- News remains on existing configured vendors.
- Deterministic runner remains the default.

## Verification

Ubuntu temp copy:

```text
/tmp/tradingagents-phase12-direct-yahoo-NwLyFG
```

Focused tests:

```text
tests/test_direct_yahoo_chart.py
tests/test_vendor_routing.py
tests/test_dataflows_config.py
```

Result:

```text
13 passed
```

Backend config tests:

```text
backend/tests/test_tradingagents_runner.py
```

Result:

```text
6 passed
```

Live bounded data check:

```text
SPY 2026-06-18
```

Result:

```text
Stock data for SPY from 2026-06-18 to 2026-06-18
Total records: 1
Data source: Yahoo Finance chart endpoint
```

## Decision

Proceed to repeat the guarded `SPY` real-runner smoke after this market-data fix is committed.

Do not expand to `QQQ` yet.

## Boundary

- No broker integration was added.
- No live execution was added.
- No live-trading UI control was added.
- No scheduled provider-backed research job was added.
- No automatic retry loop was added.
- No paper-to-live workflow was added.
- No secret values were read, printed, copied, or recorded.
