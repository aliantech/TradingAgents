# Phase 2B Scheduler Runner

## Purpose

Provide a small scheduler runner boundary for AQuantLens US market-data sync targets.

This runner is intended for cron, systemd timers, or a future worker process. It does not place trades and does not require broker permissions.

## Target Format

Configure targets with:

```text
SYMBOL:timeframe:lookback_days
```

Examples:

```text
SPY:1d:2
SPY:1d:2,QQQ:5m:1
```

Supported timeframes:

- `1m`
- `5m`
- `1d`

`lookback_days` is inclusive. For example, `SPY:1d:2` with `today=2026-06-17` syncs `2026-06-16` through `2026-06-17`.

## Configuration

Default config:

```text
AQUANTLENS_SCHEDULER_TARGETS=SPY:1d:2
```

Provider config still uses:

```text
AQUANTLENS_MARKET_DATA_PROVIDER=sample
```

Use `polygon` only after provider environment variables are available in the runtime environment. Do not print or log secret values.

## Run Once

From the backend environment:

```bash
python -m app.market_data.cli run-scheduler-once --provider sample --targets "SPY:1d:2,QQQ:5m:1" --today 2026-06-17
```

The command prints JSON, one item per configured target:

```json
[
  {"symbol": "SPY", "timeframe": "1d", "status": "succeeded", "rows_written": 2, "error_message": null}
]
```

Exit code:

- `0` when all targets succeed.
- `1` when at least one target fails.

## Observability

After a run, inspect:

- `GET /api/market-data/sync-runs`
- `GET /api/market-data/sync-summary`
- `GET /api/market-data/sync-summary/groups`
- `GET /api/market-data/sync-health`

The frontend data-source sync panel also shows summary, grouped metrics, recent history, and schedule health.

## Safety

- No broker integration.
- No order placement.
- No AI trading authority.
- No secret values should be read, printed, copied, or committed.
