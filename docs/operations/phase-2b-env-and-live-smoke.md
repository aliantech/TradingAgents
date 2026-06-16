# Phase 2B Env Setup and Live Smoke

## Scope

This document describes local development setup and smoke-test commands for Phase 2B market data sync.

Do not write real API keys, tokens, Redis passwords, broker credentials, or account identifiers into this file.

## Environment Variables

Backend settings use the `AQUANTLENS_` prefix.

```bash
export AQUANTLENS_DATABASE_URL="sqlite:///./aquantlens_us.db"
export AQUANTLENS_MARKET_DATA_PROVIDER="sample"
export AQUANTLENS_MANUAL_MARKET_SYNC_ENABLED="true"
export AQUANTLENS_REALTIME_MARKET_PUBLISH_ENABLED="false"
export AQUANTLENS_REDIS_URL="redis://127.0.0.1:6379/0"
export AQUANTLENS_REALTIME_MARKET_TTL_SECONDS="300"
```

For Polygon live smoke, set the key only in the shell/session running the backend or CLI:

```bash
export AQUANTLENS_MARKET_DATA_PROVIDER="polygon"
export AQUANTLENS_POLYGON_API_KEY="<set-in-shell-only>"
export AQUANTLENS_POLYGON_BASE_URL="https://api.polygon.io"
export AQUANTLENS_PROVIDER_MAX_RETRIES="2"
export AQUANTLENS_PROVIDER_RETRY_BACKOFF_SECONDS="1.0"
```

Never print the API key. Never commit `.env`.

## Provider Readiness Gate

Before any live-provider smoke, run:

```bash
python -m app.market_data.cli provider-readiness --provider polygon
```

Expected when configuration is missing:

```json
{"provider": "polygon", "ready": false, "missing": ["AQUANTLENS_POLYGON_API_KEY"], "message": "Polygon provider is missing required runtime configuration."}
```

Expected when runtime configuration is present:

```json
{"provider": "polygon", "ready": true, "missing": [], "message": "Polygon provider is ready for a live smoke run."}
```

The readiness command must never print secret values.

The same gate is available through:

```text
GET /api/market-data/provider-readiness?provider=polygon
```

## Phase 2B Preflight

Run non-live backend and frontend checks:

```bash
scripts/phase2b_preflight.sh
```

This runs backend tests and the frontend build, then skips live provider smoke by default.

After runtime provider env vars are available, run the same preflight with live smoke enabled:

```bash
RUN_LIVE_SMOKE=1 scripts/phase2b_preflight.sh
```

The preflight script does not read `.env` or print runtime env vars.

## Sample Provider Smoke

```bash
cd backend
. .venv/bin/activate
python -m app.market_data.cli sync-daily-bars \
  --symbol SPY \
  --start 2026-06-17 \
  --end 2026-06-17 \
  --provider sample \
  --timeframe 5m
```

Expected result:

```json
{"status": "succeeded", "rows_written": 1, "error_message": null}
```

## Polygon Live Smoke

Run only after `provider-readiness --provider polygon` returns `ready=true`.

Use the final gate command first. It runs readiness, guarded smoke, and audit-row verification in one bounded workflow.

Recommended script:

```bash
scripts/phase2b_final_live_smoke.sh
```

The script uses the current shell/session runtime env vars. It does not read `.env`.

Equivalent CLI:

```bash
python -m app.market_data.cli final-live-smoke-gate \
  --symbol SPY \
  --start 2026-06-17 \
  --end 2026-06-17 \
  --provider polygon \
  --timeframe 1d
```

Expected when configuration is missing:

```json
{"provider": "polygon", "symbol": "SPY", "timeframe": "1d", "start": "2026-06-17", "end": "2026-06-17", "status": "not_ready", "readiness_ready": false, "smoke_status": null, "rows_written": 0, "audit_rows_found": 0, "missing": ["AQUANTLENS_POLYGON_API_KEY"], "error_message": "Polygon provider is missing required runtime configuration."}
```

Expected when the provider request succeeds:

```json
{"provider": "polygon", "symbol": "SPY", "timeframe": "1d", "start": "2026-06-17", "end": "2026-06-17", "status": "succeeded", "readiness_ready": true, "smoke_status": "succeeded", "rows_written": 1, "audit_rows_found": 1, "missing": [], "error_message": null}
```

For troubleshooting, run the component commands separately:

```bash
python -m app.market_data.cli provider-readiness --provider polygon
python -m app.market_data.cli live-provider-smoke --provider polygon --symbol SPY --timeframe 1d --start 2026-06-17 --end 2026-06-17
python -m app.market_data.cli list-sync-runs --provider polygon --sync-type daily_bars --limit 5
```

The audit listing command can also be run independently:

```bash
python -m app.market_data.cli list-sync-runs --provider polygon --sync-type daily_bars --limit 5
```

Intraday guarded smoke:

```bash
python -m app.market_data.cli final-live-smoke-gate \
  --symbol SPY \
  --start 2026-06-17 \
  --end 2026-06-17 \
  --provider polygon \
  --timeframe 1m
```

SPX uses provider symbol mapping internally:

```bash
python -m app.market_data.cli final-live-smoke-gate \
  --symbol SPX \
  --start 2026-06-17 \
  --end 2026-06-17 \
  --provider polygon \
  --timeframe 1d
```

## Redis Publisher Smoke

Run only against a local or development Redis instance.

```bash
export AQUANTLENS_REALTIME_MARKET_PUBLISH_ENABLED="true"
export AQUANTLENS_REDIS_URL="redis://127.0.0.1:6379/0"

python -m app.market_data.cli sync-daily-bars \
  --symbol SPY \
  --start 2026-06-17 \
  --end 2026-06-17 \
  --provider sample \
  --timeframe 1m
```

Expected Redis writes:

- `latest:SPY`
- `stream:market_events`

## Safety Notes

- Phase 2B is market-data sync only.
- No broker order placement is implemented.
- No real-money trading is enabled.
- Manual sync API is controlled by `AQUANTLENS_MANUAL_MARKET_SYNC_ENABLED`.
- Live smoke commands should be run with minimum scope symbols and short date ranges first.
