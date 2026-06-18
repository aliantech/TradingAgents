# AQuantLens US Options Branch

## Status

Status: Phase 2C Slices 1-27 Implemented; Phase 2D Pre-Clear Complete
Last Reviewed: 2026-06-19
Owner: Yasin

## Purpose

Build a separate AQuantLens U.S.-market branch on top of the open-source TradingAgents framework: a Chinese-first AI trading research workbench for U.S. equities, indices, and selected options.

The first phase focuses on research, reporting, market data storage, and charting foundations. It deliberately avoids live automated trading until data quality, reporting reliability, quantitative validation, and risk controls are mature.

This branch is intentionally separate from the existing AQuantLens main project, which already contains broader market coverage and legacy A-share-oriented assumptions. The U.S. branch should optimize for SPX/SPY/QQQ, U.S. option-chain data, English data vendors, and Chinese research output.

## Product Direction

AQuantLens US Options Branch should become an AI trading research and quant platform with these long-term layers:

1. AI research and Chinese reporting.
2. Market data ingestion, storage, and charting.
3. Quant strategy and backtesting.
4. Paper trading and risk management.
5. Controlled live execution.

## Branch Strategy

- Git branch: `aquantlens-us`.
- Product identity: AQuantLens US Options Branch until a permanent name is chosen.
- Relationship to AQuantLens mainline: sibling branch/product direction, not a direct replacement.
- Main reason for separation: the existing AQuantLens scope includes A-share and broader workflows that are not friendly to a U.S. options-first design.

## Upstream Sync Strategy

- `main` tracks upstream `aliantech/TradingAgents` and should remain clean of AQuantLens-specific changes.
- `aquantlens-us` is the active product branch for U.S. equities, SPX/SPY/QQQ, and selected U.S. options.
- Upstream updates should be pulled into `main` first.
- After each upstream update, review changes before adapting them into `aquantlens-us`.
- Adopt upstream changes selectively when they improve model support, provider support, security, stability, data handling, or TradingAgents core behavior.
- Skip or rewrite upstream changes when they conflict with the U.S/options branch architecture, bilingual UI direction, Chinese-first reports, TimescaleDB/Redis data layer, or future quant/trading boundaries.
- Keep adaptation commits small and auditable.

## Phase 1 Goal

Deliver an MVP that can:

- Run TradingAgents analysis through a backend API.
- Generate Chinese-first structured reports.
- Provide a bilingual frontend UI.
- Save reports, agent runs, and market data.
- Display basic charts and selected option-chain data.
- Prepare clean interfaces for later quant and execution modules.

## Current Progress Snapshot

As of 2026-06-19, the branch has moved beyond the original Phase 1 foundation into Phase 2C options-data workbench implementation.

- Phase 1: architecture, product scope, API/UI module plan, and research-only safety boundary are documented.
- Phase 2A: SQLAlchemy persistence for analysis runs, reports, instruments, and market bars is implemented and documented as verified.
- Phase 2B: provider sync, Polygon/sample provider boundary, scheduler, sync audit, readiness gates, guarded smoke commands, and frontend sync visibility are documented as complete.
- Phase 2C: option contracts, option snapshots, option-chain sync, options APIs, selected contract bars API, and workbench UI slices through slice 27 are implemented in the working tree, with an additional reverse-proxy preview fix recorded in the roadmap.
- Current Phase 2C state: implementation is advanced, Ubuntu backend/frontend validation has passed, and the pre-Phase-2D Settings/provider readiness product-path cleanup is complete. Remaining work should move into Phase 2D research workflow planning and implementation.

Current code shape:

- Backend: FastAPI service boundary with analysis, reports, market data, options, settings, and health routers.
- Data layer: SQLAlchemy models for analysis/report persistence, market bars, provider sync audit, settings, option contracts, and option snapshots.
- Frontend: React/Vite/TypeScript workbench with Dashboard, Analysis, Reports, Market Data, Options, Runs, and Settings pages.
- Upstream TradingAgents: retained as the AI research framework underneath the AQuantLens US/options service and UI layers.

## Preferred Stack

Frontend:

- React + Vite + TypeScript
- shadcn/ui + Tailwind CSS
- i18next
- TanStack Table
- lightweight-charts

Backend:

- FastAPI
- TradingAgents service wrapper
- PostgreSQL + TimescaleDB
- Redis
- WebSocket or SSE for progress updates
- Background workers for market data ingestion

## Market Scope

Initial market scope:

- U.S. equities and ETFs: SPY, QQQ, AAPL, MSFT, NVDA, TSLA, AMZN, META.
- Indices: SPX, VIX.
- Options: SPX/SPXW, SPY options, QQQ options, and selected high-liquidity U.S. equity options.

Initial storage scope:

- 1m and 1d bars for equities, ETFs, and indices.
- Option contracts and option-chain snapshots.
- Option 1m and daily bars for selected contracts.
- Latest bid, ask, last, volume, open interest, implied volatility, and Greeks.

## Phase 1 Non-Goals

- No live broker order placement.
- No AI-direct trading authority.
- No full OPRA tick/quote warehouse.
- No TradingView proprietary library dependency.
- No multi-tenant SaaS architecture.
- No public investment advice positioning.

## Key Documents

- `docs/roadmap/phase-1-roadmap.md`
- `docs/architecture/phase-1-architecture.md`
- `docs/roadmap/phase-2a-roadmap.md`
- `docs/roadmap/phase-2a-verification.md`
- `docs/roadmap/phase-2b-roadmap.md`
- `docs/roadmap/phase-2b-completion-audit.md`
- `docs/roadmap/phase-2c-roadmap.md`
- `docs/roadmap/phase-2c-completion-audit.md`
- `docs/superpowers/specs/2026-06-17-aquantlens-phase-1-design.md`
- `docs/superpowers/plans/2026-06-17-aquantlens-phase-1.md`
