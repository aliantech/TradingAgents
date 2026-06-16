# Phase 2A Roadmap

## Objective

Move AQuantLens US from Phase 1 sample/in-memory behavior toward a persistent research platform.

## Scope

Phase 2A focuses on:

- Persisting analysis runs and Chinese reports through a database repository.
- Keeping the existing API contract stable for the frontend.
- Introducing SQLAlchemy models that map to the Phase 1 database schema.
- Adding a market-data ingestion service that can write normalized bars through a repository interface.
- Keeping Redis integration at the key-contract level unless a concrete realtime producer is introduced.

## Non-Goals

- No live broker integration.
- No real-money trading.
- No full OPRA quote storage.
- No full external data vendor integration yet.
- No complete backtesting engine.

## Acceptance Criteria

- Backend tests prove analysis/report data can be saved and read from a real SQLAlchemy session.
- API flow tests still pass.
- Report history survives repository access instead of relying only on a process-local dictionary.
- Market bars can be ingested through a service and read back through a repository.
- Ubuntu backend test suite passes.
- Frontend build still passes.

