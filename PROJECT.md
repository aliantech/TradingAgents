# AQuantLens US Options Branch

## Status

Status: Planning
Last Reviewed: 2026-06-17
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

- Git branch: `aquanlens-us`.
- Product identity: AQuantLens US Options Branch until a permanent name is chosen.
- Relationship to AQuantLens mainline: sibling branch/product direction, not a direct replacement.
- Main reason for separation: the existing AQuantLens scope includes A-share and broader workflows that are not friendly to a U.S. options-first design.

## Phase 1 Goal

Deliver an MVP that can:

- Run TradingAgents analysis through a backend API.
- Generate Chinese-first structured reports.
- Provide a bilingual frontend UI.
- Save reports, agent runs, and market data.
- Display basic charts and selected option-chain data.
- Prepare clean interfaces for later quant and execution modules.

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
- `docs/superpowers/specs/2026-06-17-aquantlens-phase-1-design.md`
- `docs/superpowers/plans/2026-06-17-aquantlens-phase-1.md`
