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
AQUANTLENS_SCHEDULER_INTERVAL_SECONDS=300
```

Provider config uses the live market-data provider:

```text
AQUANTLENS_MARKET_DATA_PROVIDER=polygon
```

Run scheduler sync only after provider environment variables are available in the runtime environment. Do not print or log secret values.

## Run Once

From the backend environment:

```bash
python -m app.market_data.cli run-scheduler-once --provider polygon --targets "SPY:1d:2,QQQ:5m:1" --today 2026-06-17
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

## Run Loop

For a bounded smoke test:

```bash
python -m app.market_data.cli run-scheduler-loop --provider polygon --targets "SPY:1d:2" --today 2026-06-17 --interval-seconds 1 --max-iterations 1
```

For a long-running local worker:

```bash
python -m app.market_data.cli run-scheduler-loop --provider polygon --targets "SPY:1d:2" --interval-seconds 300
```

Use an external supervisor such as systemd for restarts, logs, and process lifecycle. Keep `--max-iterations` for smoke tests and CI-like checks.

## systemd User Timer

Templates live in:

```text
infra/systemd/aquantlens-market-data-scheduler.service
infra/systemd/aquantlens-market-data-scheduler.timer
```

Install for the current Ubuntu user:

```bash
mkdir -p ~/.config/systemd/user
cp infra/systemd/aquantlens-market-data-scheduler.service ~/.config/systemd/user/
cp infra/systemd/aquantlens-market-data-scheduler.timer ~/.config/systemd/user/
systemctl --user daemon-reload
```

Run one supervised smoke:

```bash
systemctl --user start aquantlens-market-data-scheduler.service
systemctl --user status aquantlens-market-data-scheduler.service --no-pager
journalctl --user -u aquantlens-market-data-scheduler.service -n 80 --no-pager
```

Enable the timer:

```bash
systemctl --user enable --now aquantlens-market-data-scheduler.timer
systemctl --user list-timers aquantlens-market-data-scheduler.timer
```

Stop or disable:

```bash
systemctl --user stop aquantlens-market-data-scheduler.service
systemctl --user disable --now aquantlens-market-data-scheduler.timer
```

The checked-in service defaults to the `polygon` provider. Override provider, targets, database, Redis, and vendor settings in `/home/yasin/workspace/TradingAgents/backend/.env` without printing secret values.

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
