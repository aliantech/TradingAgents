# Phase 1 Data Layer

## Durable Store

Use PostgreSQL with TimescaleDB for durable Phase 1 data:

- `instruments`: U.S. equities, ETFs, indices, and future supported asset types.
- `option_contracts`: SPX/SPXW, SPY, QQQ, and selected liquid single-name option contracts.
- `market_bars`: 1m, 5m, and 1d OHLCV bars.
- `option_snapshots`: selected option-chain snapshots with IV, Greeks, volume, and open interest.
- `analysis_runs`: AI analysis job metadata and progress.
- `analysis_reports`: Chinese-first Markdown and JSON reports.
- `provider_sync_runs`: market data ingestion audit trail.

The first schema lives at `backend/app/db/schema.sql`.

## Realtime Store

Use Redis for realtime and short-lived state:

- `latest:{SYMBOL}`: latest quote snapshot.
- `chain:{UNDERLYING}:{EXPIRY}`: option-chain cache.
- `task:{analysis_id}:progress`: analysis progress state.
- `stream:market_events`: short-lived market events.
- `stream:signals`: AI or strategy signal events.

Redis key builders live in `backend/app/realtime/cache_keys.py`.

## Local Services

Run Phase 1 database services with:

```bash
docker compose -f infra/docker-compose.phase1.yml up -d
```

This starts TimescaleDB and Redis only. Backend and frontend runtime commands remain separate so development can keep short feedback loops.
