# Phase 2B Roadmap

## Objective

Build the provider-sync foundation that will later connect real U.S. market data vendors to AQuantLens US.

## Completed in First Slice

- Added `provider_sync_runs` ORM support.
- Added `ProviderSyncRepository` for sync audit writes and reads.
- Added `MarketDataSyncService` to coordinate provider fetches, bar ingestion, and sync audit records.
- Added failure-path handling so provider errors are recorded as `failed` sync runs.
- Added `GET /api/market-data/sync-runs` for recent sync history.
- Added a frontend data-source sync panel that displays provider, sync type, status, rows written, timestamp, and error messages.

## Completed in Second Slice

- Added config-driven provider selection with `AQUANTLENS_MARKET_DATA_PROVIDER`.
- Added `SampleMarketDataProvider` as the first concrete adapter boundary.
- Added provider registry lookup through `get_market_data_provider()`.
- Added CLI entrypoint:

```bash
python -m app.market_data.cli sync-daily-bars --symbol SPY --start 2026-06-16 --end 2026-06-17 --provider sample
```

- Added Redis-compatible market-data publisher boundary:
  - writes latest bar snapshot to `latest:{SYMBOL}`;
  - appends bar events to `stream:market_events`;
  - remains testable with a fake Redis client and does not require reading secrets.
- Updated ingestion so persisted bars can optionally publish realtime cache/events.
- Added manual refresh, loading state, empty state, and local error state for the frontend sync panel.

## Verification

Ubuntu backend:

```bash
cd /home/yasin/workspace/TradingAgents/backend
. .venv/bin/activate
rm -f aquanlens_us.db
pytest -q
```

Latest result:

```text
23 passed, 1 warning
```

Ubuntu frontend:

```bash
cd /home/yasin/workspace/TradingAgents/frontend
npm run build
```

Latest result:

```text
51 modules transformed
built in 138ms
```

Browser smoke:

- Opened `http://192.168.100.123:5179/`.
- Confirmed the page title is `AQuantLens`.
- Confirmed the rendered snapshot includes `数据源同步`, `刷新`, and `暂无同步记录`.

## Next Slice

- Add a concrete adapter for the first real data source.
- Add config validation and documented env-var setup without exposing secrets.
- Add scheduler wrapper around the CLI sync command.
- Add API endpoint to trigger research-only manual sync jobs in development mode.
- Add provider-specific rate-limit and retry policy.
