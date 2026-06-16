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

## Completed in Fifth Slice

- Added generic `fetch_bars(symbol, timeframe, start, end)` provider path.
- Added Polygon intraday aggregate support:
  - `1m` -> `1/minute`;
  - `5m` -> `5/minute`;
  - `1d` remains `1/day`.
- Added intraday sync support through `MarketDataSyncService.sync_bars()`.
- Added CLI `--timeframe` support for `1m`, `5m`, and `1d`.
- Added manual sync API `timeframe` support.
- Added sample provider intraday fixtures for deterministic local tests.
- Added env setup and live smoke SOP at `docs/operations/phase-2b-env-and-live-smoke.md`.

## Completed in Sixth Slice

- Added provider sync summary metrics:
  - total runs;
  - succeeded runs;
  - failed runs;
  - rows written;
  - latest status;
  - latest finished timestamp;
  - average duration in milliseconds.
- Added `GET /api/market-data/sync-summary`.
- Added frontend health metric cards to the data-source sync panel.
- Browser smoke verifies the summary updates after clicking `同步 SPY`.

## Completed in Seventh Slice

- Added provider, sync type, and time-window filters to sync runs and summary queries.
- Added API filter support for:
  - `provider`;
  - `sync_type`;
  - `started_after`;
  - `started_before`.
- Added frontend provider input and sync type selector to the data-source sync panel.
- Sync history and summary now use the same filter state.

## Completed in Eighth Slice

- Added frontend time-window filters for sync summary and history:
  - started after;
  - started before.
- Frontend converts local datetime inputs to ISO query parameters for the existing API filters.
- Browser smoke verifies the `开始` and `结束` controls render in the sync panel without layout breakage.

## Completed in Ninth Slice

- Replaced backend test extra dependency `httpx` with `httpx2>=2.4`.
- FastAPI/Starlette `TestClient` now uses Starlette's preferred `httpx2` path.
- Removed the recurring `StarletteDeprecationWarning` from backend test output.

## Completed in Tenth Slice

- Added grouped provider sync summary metrics by `provider` and `sync_type`.
- Added `GET /api/market-data/sync-summary/groups`.
- Added frontend grouped health rows to the data-source sync panel:
  - provider;
  - sync type;
  - succeeded runs over total runs;
  - failed runs;
  - rows written;
  - average duration in milliseconds.
- Kept grouped metrics on the same provider, sync type, and time-window filters as the summary cards and history list.

## Completed in Eleventh Slice

- Added provider sync health evaluation for scheduled sync targets.
- Added configurable alert thresholds:
  - `AQUANTLENS_PROVIDER_SYNC_STALE_AFTER_MINUTES`;
  - `AQUANTLENS_PROVIDER_SYNC_FAILURE_RATE_THRESHOLD`.
- Added `GET /api/market-data/sync-health`.
- Health states now cover:
  - `missing` when no run exists for the target;
  - `failing` when the latest run failed or the failure rate crosses the configured threshold;
  - `stale` when the latest successful run is older than the configured threshold;
  - `ok` when the target is current and below failure thresholds.
- Added timezone normalization in health evaluation so SQLite-backed local tests and aware API timestamps compare consistently.
- Added frontend schedule health visibility in the data-source sync panel.

## Completed in Twelfth Slice

- Added a first configured scheduler runner boundary.
- Added `AQUANTLENS_SCHEDULER_TARGETS` with `SYMBOL:timeframe:lookback_days` target format.
- Added scheduler target parsing for `1m`, `5m`, and `1d` sync targets.
- Added `run_configured_sync_targets_once()` so cron, systemd timers, or a future worker can invoke one configured sync round.
- Added CLI command:

```bash
python -m app.market_data.cli run-scheduler-once --provider sample --targets "SPY:1d:2,QQQ:5m:1" --today 2026-06-17
```

- Added scheduler runner SOP at `docs/operations/phase-2b-scheduler-runner.md`.

## Completed in Thirteenth Slice

- Added a periodic scheduler loop boundary around configured sync targets.
- Added `AQUANTLENS_SCHEDULER_INTERVAL_SECONDS`.
- Added `run_scheduler_loop()` with injectable `today_fn`, `sleep_fn`, and optional `max_iterations` for deterministic tests and bounded smoke runs.
- Added CLI command:

```bash
python -m app.market_data.cli run-scheduler-loop --provider sample --targets "SPY:1d:2" --today 2026-06-17 --interval-seconds 1 --max-iterations 1
```

- Updated scheduler runner SOP with bounded smoke and long-running worker examples.

## Verification

Ubuntu backend:

```bash
cd /home/yasin/workspace/TradingAgents/backend
. .venv/bin/activate
rm -f aquantlens_us.db
pytest -q
```

Latest result:

```text
56 passed
```

Scheduler runner targeted:

```bash
cd /home/yasin/workspace/TradingAgents/backend
. .venv/bin/activate
rm -f aquantlens_us.db
pytest tests/test_market_data_scheduler.py tests/test_market_data_cli.py -q
```

Latest result:

```text
10 passed
```

Scheduler CLI smoke:

```bash
python -m app.market_data.cli run-scheduler-once --provider sample --targets "SPY:1d:2,QQQ:5m:1" --today 2026-06-17
```

Latest result:

```text
SPY 1d succeeded with 2 rows; QQQ 5m succeeded with 1 row
```

Scheduler loop CLI smoke:

```bash
python -m app.market_data.cli run-scheduler-loop --provider sample --targets "SPY:1d:2" --today 2026-06-17 --interval-seconds 1 --max-iterations 1
```

Latest result:

```text
iteration 1: SPY 1d succeeded with 2 rows
```

Ubuntu frontend:

```bash
cd /home/yasin/workspace/TradingAgents/frontend
npm run build
```

Latest result:

```text
51 modules transformed
built in 145ms
```

Browser smoke:

- Opened `http://192.168.100.123:5185/`.
- Confirmed the page title is `AQuantLens`.
- Confirmed the initial sync health panel shows `调度状态=无记录`, `sample`, `daily_bars`, and `阈值 1440 分钟`.
- Clicked `同步 SPY`.
- Confirmed sync history API returned `sample`, `daily_bars`, `succeeded`, `2 rows`.
- Confirmed sync summary API returned `total_runs=1`, `succeeded=1`, `failed=0`, `rows_written=2`.
- Confirmed sync grouped summary API returned one group with `provider=sample`, `sync_type=daily_bars`, `total_runs=1`, `succeeded=1`, `failed=0`, and `rows_written=2`.
- Confirmed the rendered snapshot includes `总次数=1`, `成功=1`, `失败=0`, `写入=2`, `调度状态=正常`, `sample`, `daily_bars`, `1/1 成功`, `0 失败`, and `2 rows`.
- Confirmed sync health API can return `stale` when called with a deterministic `now` and a 60-minute threshold.
- Confirmed filtered API query `provider=sample&sync_type=daily_bars` returned one successful run.
- Confirmed filtered API query `provider=polygon` returned zero runs in the sample smoke database.
- Confirmed browser snapshot includes `Provider`, `类型`, `开始`, and `结束` controls.

## Next Slice

- Add live-provider smoke execution once user-provided env vars are available, without reading or printing secrets.
- Add systemd timer/service examples or deployment wiring for the scheduler loop.
