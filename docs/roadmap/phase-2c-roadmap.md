# Phase 2C Roadmap

## Objective

Build the U.S. options data foundation for AQuantLens US so the platform can store selected SPX/SPY/QQQ and liquid U.S. equity option-chain data before adding option analytics, quant models, or any trading workflow.

Phase 2C remains a data and research layer. It does not add broker order placement, AI trading authority, or live execution.

## Scope

- Option contract metadata for selected underlyings.
- Option-chain snapshot storage for bid, ask, last, volume, open interest, implied volatility, and Greeks.
- Provider-neutral repository interfaces before provider-specific adapters grow larger.
- API endpoints that expose option contracts and chain snapshots to the frontend.
- Frontend option-chain views with Chinese-first labels and English professional terms where appropriate.
- Future compatibility with option bars, volatility surfaces, strategy builders, and backtesting.

## Completed in First Slice

- Added `option_contracts` ORM model.
- Added `option_snapshots` ORM model.
- Added `OptionRepository` with:
  - contract upsert;
  - contract listing by underlying and expiry;
  - snapshot upsert;
  - chain snapshot listing by underlying and expiry.
- Added repository tests covering idempotent contract writes and idempotent snapshot updates.

## Completed in Second Slice

- Added a guarded options entitlement live smoke module:
  - checks contracts endpoint for each underlying;
  - checks option-chain snapshot endpoint for each underlying;
  - defaults to `SPY,SPX` so ETF options and index options are tested together;
  - supports configurable timeout and retry for slow option-chain responses;
  - returns JSON with `succeeded`, `partial`, `failed`, or `not_ready`.
- Added `scripts/phase2c_options_live_smoke.sh`.
- The shell script does not read `.env`, print environment variables, or expose the API key.
- Added tests for the smoke module and shell-script safety boundary.

## Completed in Third Slice

- Confirmed live Options Advanced entitlement for index options with SPX:
  - contracts endpoint succeeded;
  - option-chain snapshot endpoint succeeded;
  - no missing runtime config;
  - no HTTP 403 entitlement failure.
- Phase 2C market scope is now confirmed for:
  - ETF options: `SPY`, `QQQ`;
  - index options: `SPX`, `SPXW` direction;
  - selected liquid U.S. single-name options.

## Completed in Fourth Slice

- Connected `GET /api/options/chain` to `OptionRepository`.
- Added deterministic sample option-chain seeding for empty chains:
  - `SPY`;
  - `QQQ`;
  - `SPX`.
- API now returns persisted provider data when available and only seeds sample data when the requested chain is empty.
- Added API tests for:
  - persisted snapshot response;
  - deterministic SPX sample fallback.

## Completed in Fifth Slice

- Added a frontend option-chain control surface under `frontend`:
  - underlying selector for `SPX`, `SPY`, and `QQQ`;
  - expiry date input;
  - manual refresh action;
  - loading and error states.
- Expanded the option-chain table with:
  - last price;
  - volume;
  - IV;
  - Delta, Gamma, Theta, Vega;
  - open interest;
  - source.
- Added summary metrics for contract count, total volume, total open interest, and latest timestamp.
- Kept the UI Chinese-first while preserving professional terms such as IV, Greeks, Volume, and Open Interest.

## Completed in Sixth Slice

- Added `PolygonOptionsProvider` for Massive/Polygon option-chain snapshot payloads.
- Converted option-chain snapshot rows into:
  - `OptionContractRecord`;
  - `OptionSnapshotRecord`.
- Added `OptionChainSyncService` to persist option contracts, snapshots, and `provider_sync_runs` audit records.
- Added tests for:
  - Polygon/Massive option-chain snapshot parsing;
  - option-chain sync persistence and audit writes.

## Completed in Seventh Slice

- Added guarded manual option-chain sync API:
  - `POST /api/options/sync-chain`;
  - uses `OptionChainSyncService`;
  - protected by `AQUANTLENS_MANUAL_MARKET_SYNC_ENABLED`.
- Added frontend action `同步期权链` on the option-chain panel.
- UI action refreshes the option chain and sync health/history after completion.
- CLI remains an operations-only thin entrypoint and is not the daily product workflow.

## Completed in Eighth Slice

- Added thin operations CLI module:
  - `python -m app.options.cli sync-chain`;
  - readiness guard before provider access;
  - calls `OptionChainSyncService`;
  - emits JSON for CI, scheduler, and shell smoke usage.
- Added `scripts/phase2c_options_sync_live_smoke.sh`.
- Default live sync smoke expiry is `2026-06-19` to avoid expired-chain empty results.
- Empty provider responses now record `status=empty` instead of `succeeded`.
- The script does not read `.env`, print environment variables, or expose the API key.
- Added tests for:
  - CLI service delegation;
  - no-key guarded output;
  - script safety boundary.

## UI And CLI Boundary

- UI is the daily product entrypoint for research workflows, option-chain inspection, and later manual data actions.
- CLI remains a thin engineering/operations entrypoint for:
  - provider smoke tests;
  - CI verification;
  - cron/systemd scheduled sync;
  - one-off backfills;
  - server-side diagnostics when the UI is unavailable.
- Business logic should live in provider/service/repository modules, not inside CLI commands.

## Verification

Ubuntu backend verification:

```bash
pytest tests/test_options_repository.py -q
pytest tests/test_options_api.py -q
pytest tests/test_options_polygon_provider.py tests/test_options_sync.py -q
pytest tests/test_options_sync_api.py -q
pytest tests/test_options_cli.py tests/test_phase2c_options_sync_live_smoke_script.py -q
pytest tests/test_options_live_smoke.py tests/test_phase2c_options_live_smoke_script.py -q
pytest -q
```

Results:

- Targeted options repository tests: `2 passed`.
- Targeted options API tests: `2 passed`.
- Targeted options ingestion tests: `2 passed`.
- Targeted options sync API tests: `2 passed`.
- Targeted options CLI/smoke tests: `4 passed`.
- Targeted options live smoke tests: `4 passed`.
- Timeout/retry options live smoke tests: `5 passed`.
- Full backend suite: `91 passed`.
- Frontend production build: `npm run build` succeeded.
- Guarded no-key smoke returns `status=not_ready` with missing `AQUANTLENS_POLYGON_API_KEY`.
- Guarded no-key option-chain sync smoke returns `status=not_ready` with missing `AQUANTLENS_POLYGON_API_KEY`.
- Live sync with expired `2024-06-21` returned `rows_written=0`; this now maps to `status=empty`.

## Live Entitlement Check

Run this in a runtime shell/session where `AQUANTLENS_POLYGON_API_KEY` is already provided:

```bash
scripts/phase2c_options_live_smoke.sh
```

Optional custom underlyings:

```bash
scripts/phase2c_options_live_smoke.sh SPY,QQQ,SPX
```

For a slow index option-chain response, run SPX alone with a longer timeout:

```bash
scripts/phase2c_options_live_smoke.sh SPX 90 1
```

Interpretation:

- `SPY` success verifies ETF options access.
- `SPX` success verifies index options access.
- `partial` means the endpoint was reachable but one side returned an empty result.
- `failed` with HTTP 403 means the plan, ticker, or endpoint access needs entitlement review.
- `failed` with a read timeout is inconclusive; rerun the underlying alone with a longer timeout before judging entitlement.

Observed first live run:

- `SPY` contracts and chain snapshot succeeded.
- `SPX` did not return 403 or empty; the request timed out, so index-options entitlement remains inconclusive until a longer SPX-only check completes.

Confirmed SPX-only live run:

```bash
scripts/phase2c_options_live_smoke.sh SPX 90 1
```

Result:

- `status=succeeded`
- `readiness_ready=true`
- `contracts_status=succeeded`
- `chain_snapshot_status=succeeded`
- `missing=[]`
- `error_message=null`

## WebSocket Note

Massive WebSocket docs describe Options streams as real-time OPRA trades, quotes, and aggregates. WebSocket ingestion is useful for future realtime cache/events, but Phase 2C should first validate REST entitlement and persistence because REST responses are easier to audit and replay.

## Next Slice

- Add live guarded SPX/SPY option-chain sync smoke once the runtime shell has the API key loaded.
- Add scheduler/backfill target config only after live option-chain sync smoke is stable.
