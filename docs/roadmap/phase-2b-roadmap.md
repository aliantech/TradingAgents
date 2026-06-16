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

## Completed in Third Slice

- Added a Polygon-style provider adapter boundary:
  - aggregate daily-bars payload parsing;
  - API key validation without reading or exposing secrets;
  - retry handling for rate limits and temporary provider transport failures.
- Added provider config:
  - `AQUANTLENS_POLYGON_API_KEY`;
  - `AQUANTLENS_POLYGON_BASE_URL`;
  - `AQUANTLENS_PROVIDER_MAX_RETRIES`;
  - `AQUANTLENS_PROVIDER_RETRY_BACKOFF_SECONDS`.
- Added scheduler wrapper through `run_daily_bar_sync_schedule()`.
- Added research/development manual sync API:

```text
POST /api/market-data/sync-daily-bars
```

- Added `AQUANTLENS_MANUAL_MARKET_SYNC_ENABLED` kill switch for the manual sync API.
- Added frontend `同步 SPY` action that triggers sample daily-bars sync, refreshes sync history, and reloads market context.

## Completed in Fourth Slice

- Added provider-specific symbol mapping:
  - Polygon `SPX` maps to `I:SPX`;
  - `SPY`, `QQQ`, and selected U.S. single-name equities keep normal ticker symbols.
- Added runtime Redis publisher factory:
  - controlled by `AQUANTLENS_REALTIME_MARKET_PUBLISH_ENABLED`;
  - uses `AQUANTLENS_REDIS_URL`;
  - applies `AQUANTLENS_REALTIME_MARKET_TTL_SECONDS`;
  - defaults to disabled so local sync does not require Redis.
- Added `redis>=5.0` backend dependency for runtime publisher binding.
- Connected `run_sync_daily_bars()` to optional realtime publishing through `MarketDataIngestionService`.

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
37 passed, 1 warning
```

Ubuntu frontend:

```bash
cd /home/yasin/workspace/TradingAgents/frontend
npm run build
```

Latest result:

```text
51 modules transformed
built in 231ms
```

Browser smoke:

- Opened `http://192.168.100.123:5180/`.
- Confirmed the page title is `AQuantLens`.
- Clicked `同步 SPY`.
- Confirmed sync history API returned `sample`, `daily_bars`, `succeeded`, `2 rows`.
- Confirmed the rendered snapshot includes `sample`, `daily_bars`, and `2 rows`.

## Next Slice

- Add intraday `1m/5m` provider path after daily-bars behavior is stable.
- Add documented env-var setup for local development without exposing secrets.
- Add dependency pinning cleanup for the FastAPI/Starlette `TestClient` warning.
- Add live-provider smoke procedure that uses user-provided env vars without reading or printing secrets.
