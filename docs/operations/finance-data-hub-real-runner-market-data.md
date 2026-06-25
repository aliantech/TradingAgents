# Finance Data Hub Real-Runner Market Data

Date: 2026-06-26

## Scope

TradingAgents real-runner market OHLCV should not call Yahoo/yfinance directly. Market bars are read through Finance Data Hub.

This affects:

- `get_stock_data`
- `get_indicators`
- verified market-data snapshots
- deferred reflection outcome return calculation

## Implementation

- Added the `finance_data_hub` TradingAgents dataflow vendor.
- Registered `finance_data_hub` for stock bars and indicator OHLCV.
- Removed the active `direct_yahoo_chart` dataflow vendor and its tests.
- Configured the real TradingAgents runner to use `finance_data_hub`.
- Changed real-runner evidence label to `finance-data-hub-verified-snapshot`.

## Contract

The dataflow uses the Finance Data Hub asset contract:

1. `GET /assets/{symbol}` to resolve `asset_id`.
2. `GET /assets/{asset_id}/bars?timeframe=1d&start=YYYY-MM-DD&end=YYYY-MM-DD`.

## Boundary

Futu, IBKR, Polygon/Massive, Yahoo, and other vendor integrations belong upstream in Finance Data Hub. TradingAgents consumes normalized Hub data.
