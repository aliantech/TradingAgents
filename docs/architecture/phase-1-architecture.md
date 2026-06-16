# Phase 1 Architecture

This architecture is for the AQuantLens US Options Branch. It is intentionally separate from the existing AQuantLens mainline so the data model, vendor choices, and product workflows can optimize for U.S. equities, SPX/SPY/QQQ, and options.

## High-Level Architecture

```text
React/Vite Frontend
  -> FastAPI Backend
    -> TradingAgents Service Wrapper
    -> Market Data Service
    -> Report Service
    -> PostgreSQL/TimescaleDB
    -> Redis
    -> Background Workers
```

## Frontend Modules

- `Dashboard`: overview of watchlist, latest analyses, and system status.
- `Analysis`: symbol input, model/provider selection, analysis depth, progress, and generated report.
- `Reports`: saved report history and report detail view.
- `Market Data`: K-line, intraday chart, volume, and indicators.
- `Options`: option-chain table, expiry selector, Greeks, IV, volume, and open interest.
- `Settings`: providers, model defaults, language, and data-source configuration.

## Backend Modules

- `analysis`: starts and tracks TradingAgents jobs.
- `reports`: stores Markdown and JSON report artifacts.
- `market_data`: normalizes provider data and serves historical bars.
- `options`: stores contracts and selected option-chain snapshots.
- `realtime`: streams job progress and market updates.
- `settings`: stores runtime configuration that is safe to persist.

## Data Storage

Use PostgreSQL with TimescaleDB hypertables for time-series data.

Core tables:

- `instruments`
- `option_contracts`
- `market_bars`
- `option_snapshots`
- `analysis_runs`
- `analysis_reports`
- `provider_sync_runs`

Redis responsibilities:

- `latest:{symbol}` for latest market quote snapshot.
- `chain:{underlying}:{expiry}` for option-chain cache.
- `task:{analysis_id}:progress` for analysis progress.
- `stream:market_events` for short-lived market events.
- `stream:signals` for AI/strategy signal events.

## Market Data Policy

Phase 1 focuses on selected U.S. symbols and selected option contracts:

- U.S. equities and ETFs: SPY, QQQ, AAPL, MSFT, NVDA, TSLA, AMZN, META.
- Indices: SPX, VIX.
- Options: SPX/SPXW, SPY, QQQ, and selected liquid single-name options.

Store:

- 1m and 1d bars.
- Option contracts.
- Option-chain snapshots for selected expiries and strike ranges.
- Latest quote fields and Greeks when provider supports them.

Do not store:

- Full OPRA tick/quote feed.
- All expiries and all strikes for every underlying.
- Broker account or order data in Phase 1.

## Report Policy

Reports are Chinese-first. Professional terms may remain English or mixed:

- Greeks
- IV
- delta/gamma/theta/vega
- Sharpe Ratio
- max drawdown
- MACD
- RSI

Every report should be saved in both Markdown and JSON form. JSON is required for future search, statistics, backtesting, and strategy extraction.

## Safety Boundary

AI outputs may inform research and generate trade plans, but they must not directly place orders.

Future live trading must pass through:

```text
Signal
-> Risk Engine
-> Position Sizing
-> Execution Conditions
-> Broker Adapter
-> Audit Log
```
