# Phase 2C Roadmap

## Objective

Build the U.S. options data foundation for AQuantLens US so the platform can store selected SPX/SPY/QQQ and liquid U.S. equity option-chain data before adding option analytics, quant models, or any trading workflow.

Phase 2C remains a data and research layer. It does not add broker order placement, AI trading authority, or live execution.

Completion audit draft: `docs/roadmap/phase-2c-completion-audit.md`.

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

## Completed in Ninth Slice

- Initialized the frontend as a real shadcn/ui + Tailwind v4 Vite project:
  - added `components.json`;
  - added shadcn UI primitives under `frontend/src/components/ui`;
  - configured Vite and TypeScript aliases for `@/*`.
- Reworked the frontend into the project-defined workbench route:
  - Dashboard / 研究驾驶舱;
  - Analysis / AI 分析;
  - Reports / 研究报告;
  - Market Data / 行情数据;
  - Options / 期权链;
  - Runs / 任务中心;
  - Settings / 设置.
- Migrated the app shell and core panels toward shadcn primitives:
  - `Button`;
  - `Card`;
  - `Input`;
  - `Badge`;
  - `Alert`;
  - `Table`;
  - `Separator`.
- Added route-stack dependencies from the approved UI direction:
  - `lightweight-charts`;
  - `@tanstack/react-table`.
- Replaced the temporary SVG market chart with a `lightweight-charts` candlestick chart wrapper.
- Migrated the provider sync run table to TanStack Table while keeping shadcn table rendering.
- Migrated the Options page control surface to shadcn `Select` and `ToggleGroup`.
- Preserved the Phase 2C options workflow as the priority page and surfaced:
  - Polygon/provider readiness;
  - options sync health;
  - latest `options_chain` sync run.

## Completed in Tenth Slice

- Reduced frontend bundle risk by lazy-loading heavy route components:
  - `KlineChart`;
  - `OptionChainTable`.
- Confirmed the production build now emits split chunks for:
  - `KlineChart`;
  - `OptionChainTable`;
  - main app shell.
- Reduced the previous single-bundle risk after route splitting.
- Migrated the Options page Call / Strike / Put table to TanStack Table row and column models while preserving:
  - grouped Call / Strike / Put headers;
  - ATM marker row;
  - Bid / Ask / Last interaction previews;
  - moneyness cell styling.
- Kept shadcn table rendering around the TanStack model.

## Completed in Eleventh Slice

- Upgraded the Reports detail surface toward the project UI spec:
  - fixed research-only risk notice band;
  - report metadata badges;
  - structured module tabs;
  - Markdown reader tab;
  - JSON inspection tab;
  - Markdown and JSON download actions.
- Kept PDF/DOCX export deferred because the backend does not yet expose those artifacts.

## Completed in Twelfth Slice

- Upgraded the Analysis launch surface toward the project UI spec:
  - analysis date input;
  - model/provider selector;
  - model selector tied to provider choice;
  - research depth segmented control;
  - analyst/team segmented control.
- Replaced the hard-coded frontend analysis request with a typed payload that sends:
  - symbol;
  - inferred asset type;
  - analysis date;
  - UI language;
  - LLM provider;
  - model;
  - depth.
- Kept analyst/team selection as a frontend workflow state until the backend TradingAgents orchestration contract supports that mapping.
- Synced the frontend workspace to the Ubuntu runtime workspace so the running Vite dev server can show the latest UI.

## Completed in Thirteenth Slice

- Added a backend analysis-runs list contract for the task center:
  - `GET /api/analysis/runs`;
  - persisted repository-backed runs;
  - in-memory fallback for runs not yet flushed to the repository.
- Added test coverage for the analysis-runs API contract.
- Upgraded the Runs page so it now separates:
  - AI analysis runs with All / Running / Completed / Failed filters;
  - provider sync runs and grouped provider summary metrics.
- Kept provider sync visibility on the same page because market-data readiness is part of the research workflow.

## Completed in Fourteenth Slice

- Upgraded the Market Data page toward the project UI spec:
  - symbol control;
  - `1m` / `5m` / `1d` timeframe selector;
  - explicit refresh action;
  - current bars, source, latest close, and timeframe metrics;
  - recent bars preview table.
- Replaced the frontend hard-coded `1m` market-data request with a typed timeframe-aware API adapter.
- Added a volume histogram pane to the `lightweight-charts` candlestick chart.
- Verified the Ubuntu preview stack with:
  - frontend preview `http://127.0.0.1:3013/`;
  - latest-code backend preview `http://127.0.0.1:8022/`;
  - `GET /api/market-data/bars?symbol=SPY&timeframe=5m`.

## Completed in Fifteenth Slice

- Upgraded the Settings page toward the project UI spec:
  - backend health check from `/api/health`;
  - market provider readiness;
  - options provider readiness;
  - current UI language preference;
  - model default summary from the analysis launch configuration;
  - data-source sync health;
  - recent provider sync runs.
- Kept the settings surface operational and narrow:
  - no secret values;
  - write-only frontend API key save through `/api/settings`;
  - automatic provider readiness refresh after settings are saved;
  - only safe missing configuration names from readiness responses;
  - no broker, live-trading, or paper-trading controls.
- Verified frontend builds locally and in the Ubuntu runtime workspace.

## Completed in Sixteenth Slice

- Upgraded the Dashboard toward the project UI spec:
  - supported-symbol quick selection for the research flow;
  - compact Market Pulse tiles for `SPY`, `QQQ`, `SPX`, and `VIX`;
  - sparkline price visualization from real market-bar API responses;
  - latest close, source, and change percentage in each pulse tile;
  - Research Queue for running and failed analysis runs.
- Kept Dashboard cards tied to real workflows:
  - research launch;
  - options inspection;
  - market data page;
  - runs/task center;
  - reports.
- Verified the Ubuntu preview stack can fetch daily market bars for Dashboard pulse data.

## Completed in Seventeenth Slice

- Upgraded the Options page toward the Phase 2C priority UI spec:
  - interactive expiry strip with suggested expiries;
  - expiry tab clicks load the selected option-chain date through the existing chain API;
  - selected contract metadata strip for side, expiry, and strike;
  - selected contract underlying and timestamp details;
  - selected contract historical-bars panel placeholder.
- Kept the option-bars panel honest:
  - the UI reserves the selected-contract bars area;
  - it clearly states that a backend contract-bars API is still required before chart data can appear.
- Verified the Ubuntu preview stack can fetch a non-default expiry chain.

## Completed in Eighteenth Slice

- Upgraded the App Shell top header toward the project UI spec:
  - sticky top header;
  - reusable symbol search control;
  - supported-symbol suggestions for the U.S/options branch universe;
  - U.S. market session state based on America/New_York market hours;
  - provider readiness badge;
  - language switch in the header.
- Kept the shell workflow-oriented:
  - symbol context remains available while moving between analysis, runs, reports, market data, and options;
  - provider and session state stay visible without adding unrelated admin navigation.
- Verified frontend builds locally and in the Ubuntu runtime workspace.

## Completed in Nineteenth Slice

- Upgraded Reports and Runs workflow actions:
  - report history now enriches each report with source run metadata when available;
  - report list shows run status, confidence, run id, model/provider, depth, and analysis date;
  - Runs table now exposes a real `打开报告` action for completed runs with reports;
  - running and failed rows surface progress/error action states until backend retry/log contracts exist.
- Kept actions inside research-only boundaries:
  - no broker actions;
  - no live execution;
  - no retry mutation until a safe backend retry contract exists.
- Verified Ubuntu preview APIs for analysis runs and reports.

## Completed in Twentieth Slice

- Added the selected option contract bars contract:
  - `GET /api/options/bars`;
  - timeframe support for `1m`, `5m`, and `1d`;
  - persisted option bars through the existing market-bar repository when available;
  - deterministic sample fallback when no contract bars exist yet.
- Added backend tests for:
  - persisted option-bar reads;
  - sample fallback behavior.
- Connected the Options selected-contract panel to the new contract bars API:
  - selected contract loads bars on Bid / Ask / Last inspection;
  - timeframe toggle reloads selected option bars;
  - panel shows source, bar count, latest close, volume, and sparkline.
- Verified the Ubuntu preview backend exposes `/api/options/bars`.

## Completed in Twenty-First Slice

- Upgraded Runs progress inspection:
  - frontend API adapter now exposes `GET /api/analysis/{id}`;
  - Runs table actions load analysis status for completed, running, and failed runs;
  - detail panel shows symbol, status, asset type, language, and progress events;
  - failed/running rows now have actionable progress/error detail buttons instead of static labels.
- Kept retry deferred until a safe backend retry mutation exists.
- Verified the Ubuntu preview backend returns analysis status payloads for Runs detail.

## Completed in Twenty-Second Slice

- Upgraded the App Shell navigation behavior:
  - desktop sidebar can collapse to a compact rail;
  - mobile header exposes a menu button;
  - mobile navigation opens as an overlay panel;
  - navigation selection closes the mobile overlay.
- Kept the shell aligned with the workbench route:
  - primary navigation remains shallow and focused;
  - no unrelated admin, SaaS, billing, or broker routes were added.
- Verified frontend builds locally and in the Ubuntu runtime workspace.

## Completed in Twenty-Third Slice

- Added analysis run timing metadata:
  - backend run model now carries `created_at` and `updated_at`;
  - `GET /api/analysis/runs` exposes those timestamps;
  - persisted repository reads preserve database timestamps.
- Upgraded Runs and Reports metadata:
  - Runs table shows started time;
  - Runs table computes duration from created/updated timestamps;
  - Report history uses source run created time when available.
- Verified Ubuntu backend tests and frontend build after the contract change.

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
- Full backend suite: `102 passed`.
- Frontend production build: `npm run build` succeeded.
- Frontend vendor code splitting now emits separate vendor chunks for React/i18n, Radix, icons, TanStack Table, and shared vendor code.
- Latest Ubuntu build main app chunk is about `160.41 kB`, down from about `564 kB`; the previous chunk-size warning is gone.
- Guarded no-key smoke returns `status=not_ready` with missing `AQUANTLENS_POLYGON_API_KEY`.
- Guarded no-key option-chain sync smoke returns `status=not_ready` with missing `AQUANTLENS_POLYGON_API_KEY`.
- Guarded live option-chain sync smoke on Ubuntu currently returns `status=not_ready` because `AQUANTLENS_POLYGON_API_KEY` is not configured.
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

## Phase 2D Pre-Clear

- Treat the frontend Settings workbench and `/api/settings` as the default product path for provider API keys.
- Keep CLI env-based live smoke as an optional operations check after a user has configured credentials and entitlement; do not block product planning on Mac or shell-local key injection.
- Make provider-not-ready states actionable in Market Data and Options by linking users back to Settings.
- Add scheduler/backfill target config only after the product path can save provider credentials, refresh readiness, and start sync actions without exposing secret values.

## UI Framework Slice

The AQuantLens US/options UI framework now follows the local UI design route:

- React/Vite/TypeScript frontend with shadcn/ui primitives, Tailwind, TanStack Table, lightweight-charts, and i18next.
- Added a `frontend/src/components/workbench` component layer for shadcn-composed, Tremor-inspired data-workbench primitives such as metric and status cards.
- Workbench-first shell with collapsible sidebar, sticky status header, symbol search, market/session badge, provider readiness, and language switching.
- Bilingual coverage now includes the shell plus the core Dashboard, Analysis, Reports, Options, Market Data, Runs, and Settings workflows; Chinese-first report content remains unchanged while UI labels can switch languages.
- Primary routes: Dashboard, AI Analysis, Reports, Market Data, Options, Runs, and Settings.
- Dashboard is composed from real module summaries: market bars, analysis runs, reports, option snapshots, sync health, and provider readiness.
- Analysis page includes Phase 1 supported-market validation before starting a research run.
- Analyst/team selection is now part of the backend analysis contract and persists into run metadata and report metadata.
- Options page includes underlying/expiry controls, moneyness filters, Call/Strike/Put rows, selected contract details, and selected option bars.
- Options quote interactions use Bid/Ask/Last inspection language only; Buy/Sell preview wording was removed to avoid implying broker or execution actions.
- Runs page includes running/completed/failed/all analysis run views plus progress/error inspection.
- Reports page supports Chinese-first Markdown reading and JSON inspection.
- Settings remains operational and avoids displaying secret values.
- Settings and Dashboard detail panels now use i18next-backed labels and fallback messages.
- The stable options contracts API is exposed as `GET /api/options/contracts`, with frontend adapter coverage through `listOptionContracts`.

Ubuntu preview sync was verified on 2026-06-17:

- Frontend preview: `http://127.0.0.1:3013/`
- Backend API: `http://127.0.0.1:8022/`
- Ubuntu frontend build: `npm run build` succeeded.
- Ubuntu backend targeted tests: `tests/test_analysis_api_persistence.py` and `tests/test_options_api.py` passed.
- API smoke checks passed for health, analysis runs, market bars, option contracts, option chain, and selected option bars.

Known UI follow-ups:

- Add retry mutation for failed analysis runs only after the backend exposes a safe retry contract.

## Completed in Twenty-Fourth Slice

- Connected the frontend Options workflow to the stable option-contract metadata API:
  - `GET /api/options/contracts`;
  - current underlying and expiry now load snapshots and contract metadata together.
- Added a Contract Universe widget on the Options page:
  - Call/Put contract counts;
  - expiry count;
  - strike range;
  - metadata source.
- Updated the empty option-chain state so it distinguishes:
  - no live contract metadata;
  - contract metadata exists but quote / Greeks snapshots are missing.
- Added option-contract context to the Analysis Research Context widget so TradingAgents launch checks can see both snapshots and contract metadata.
- Fixed local preview API routing:
  - local pages without `VITE_API_BASE_URL` now default to `http://127.0.0.1:8022`;
  - public non-local pages still use same-origin `/api` routes and do not point visitor browsers at localhost.
- Verified the in-app browser against `http://127.0.0.1:5173`:
  - Options page shows Contract Universe from backend data;
  - Analysis page shows Option Contracts in Research Context;
  - no `Failed to fetch`, no `API response was not JSON`, no `Research Only`, and no raw i18n keys.

## Completed in Twenty-Fifth Slice

- Surfaced option-contract coverage on the Dashboard Options Watch widget:
  - option snapshot count;
  - option contract count;
  - option volume;
  - expiry count;
  - Call / Put coverage;
  - strike range.
- Added the same contract count to the Dashboard symbol research prompt context so the first screen shows whether the selected options universe is actually ready.
- Verified the in-app browser against `http://127.0.0.1:5173/#dashboard`:
  - Dashboard shows `Option Contracts`;
  - Dashboard shows `Call / Put`;
  - Dashboard shows `Strike Range`;
  - no `Failed to fetch`, no `API response was not JSON`, and no raw i18n keys.

## Completed in Twenty-Sixth Slice

- Cleaned duplicate Dashboard surfaces after UI review:
  - removed the global module entry dock from the Dashboard because Research Pipeline already serves as the dashboard workflow entry;
  - removed the duplicate Provider / Bars / Options Sync / Latest Sync status strip from the Dashboard;
  - removed duplicate option snapshot / contract / volume metrics from the symbol research prompt card.
- Kept option readiness metrics in a single place on Dashboard:
  - Options Watch.
- Verified the in-app browser against `http://127.0.0.1:5173/#dashboard`:
  - Research Pipeline appears once;
  - Option Snapshots appears once;
  - Option Contracts appears once;
  - no `Failed to fetch`, no `API response was not JSON`, and no raw i18n keys.

## Completed in Twenty-Seventh Slice

- Removed remaining Dashboard explanatory subtitles and annotations:
  - page-header nav description;
  - sidebar item helper text;
  - sidebar bottom annotation card;
  - Dashboard card description rows.
- Removed the leftover Dashboard description i18n keys for the deleted copy.
- Kept the required operational widgets and controls:
  - Research Pipeline;
  - symbol research prompt;
  - Market Pulse;
  - Research Queue;
  - AI Findings;
  - Options Watch.
- Verified `http://127.0.0.1:5173/#dashboard` with Chrome automation:
  - old dock annotation is gone;
  - Dashboard descriptions are gone;
  - nav subtitles are gone;
  - core widgets remain visible.

## Reverse Proxy Preview Fix

On 2026-06-17, the `dash.aquantlens.com` preview showed the frontend but failed to load runtime data in a public browser.

Root cause:

- The backend reverse proxy was healthy: `https://dash.aquantlens.com/api/health` returned 200.
- Market bars were available through the public API: `GET /api/market-data/bars?symbol=SPY&timeframe=1d` returned 500 SPY daily bars.
- The frontend Vite dev server had injected `VITE_API_BASE_URL=http://127.0.0.1:8022`, causing public browsers to request the visitor machine's localhost instead of the server reverse proxy.

Fix:

- Added `resolveApiBaseUrl` so non-localhost pages ignore localhost API base URLs and use same-origin `/api` routes.
- Restarted the Ubuntu `3013` frontend preview without the localhost API override.

Verification:

- `node --experimental-strip-types frontend/src/lib/apiBaseUrl.test.ts` passed on Mac and Ubuntu.
- `npm run build` passed on Mac and Ubuntu.
- `https://dash.aquantlens.com/api/market-data/bars?symbol=SPY&timeframe=1d` returned 500 persisted bars from `aquantlens-main`.
