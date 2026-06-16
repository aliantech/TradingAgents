# Phase 2A Persistence and Ingestion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace Phase 1 in-memory/sample-only backend state with database-backed analysis/report persistence and a testable market-bar ingestion path.

**Architecture:** Add SQLAlchemy models and repositories under `backend/app/db/`, then route analysis/report APIs through repository-backed services. Keep FastAPI contracts stable so the existing React workbench keeps working. Use SQLite in tests for fast repository verification while preserving the PostgreSQL/TimescaleDB schema for deployment.

**Tech Stack:** Python, FastAPI, SQLAlchemy 2.x, Pydantic, pytest, PostgreSQL/TimescaleDB schema, SQLite test sessions.

---

## File Structure

```text
backend/app/db/
  base.py
  models.py
  session.py
backend/app/analysis/
  repository.py
  service.py
backend/app/reports/
  repository.py
  router.py
backend/app/market_data/
  repository.py
  ingestion.py
backend/tests/
  test_analysis_repository.py
  test_market_data_ingestion.py
```

## Tasks

### Task 1: SQLAlchemy DB Foundation

- [x] Write `backend/tests/test_analysis_repository.py` with a SQLite session fixture that expects `AnalysisRepository.save_run()` and `get_run()` to persist a completed analysis run with report JSON.
- [x] Run `pytest backend/tests/test_analysis_repository.py -q` on Ubuntu and confirm it fails because repository/models are missing.
- [x] Add SQLAlchemy dependency to `backend/pyproject.toml`.
- [x] Create `backend/app/db/base.py`, `models.py`, and `session.py`.
- [x] Create `backend/app/analysis/repository.py`.
- [x] Run the targeted test and confirm it passes.
- [x] Commit with `feat: add database-backed analysis repository`.

### Task 2: Wire Analysis and Reports to Repository

- [x] Add tests proving POST `/api/analysis`, GET `/api/analysis/{id}`, GET `/api/reports`, and GET `/api/reports/{id}` still work when the service uses the repository.
- [x] Refactor `backend/app/analysis/service.py`, `router.py`, and `backend/app/reports/router.py` so reads and writes go through the repository abstraction.
- [x] Keep the process-local fallback only as an explicit test/development fallback when no database session is configured.
- [x] Run all backend tests and confirm they pass.
- [x] Commit with `feat: persist analysis reports through repository`.

### Task 3: Market Bar Repository and Ingestion Service

- [x] Write `backend/tests/test_market_data_ingestion.py` with SQLite-backed tests for ingesting sample `MarketBar` rows and reading them by symbol/timeframe.
- [x] Run the targeted test and confirm it fails because repository/ingestion code is missing.
- [x] Create `backend/app/market_data/repository.py`.
- [x] Create `backend/app/market_data/ingestion.py`.
- [x] Update market-data API to read from repository when data exists, falling back to deterministic sample bars only when repository is empty.
- [x] Run targeted market-data tests and all backend tests.
- [x] Commit with `feat: add market bar ingestion repository`.

### Task 4: Verification and Documentation

- [x] Update `docs/architecture/data-layer-phase-1.md` with Phase 2A persistence status.
- [x] Add `docs/roadmap/phase-2a-verification.md` with exact commands and results.
- [x] Run Ubuntu `pytest -q`.
- [x] Run Ubuntu frontend `npm run build`.
- [ ] Commit docs with `docs: record phase two a verification`.
- [ ] Push `aquanlens-us`.

## Self-Review

- Spec coverage: persistence, report history, market-bar ingestion, tests, and docs are covered.
- Placeholders: none.
- Scope boundary: no live trading, no full external vendor, no OPRA tick store, no backtesting engine.
