# AQuantLens US Options Branch

## Status

Status: Phase 8 Research Operations Hardening Planning
Last Reviewed: 2026-06-20
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

As of 2026-06-20, the branch has moved beyond the original Phase 1 foundation into Phase 2C options-data workbench implementation.

- Phase 1: architecture, product scope, API/UI module plan, and research-only safety boundary are documented.
- Phase 2A: SQLAlchemy persistence for analysis runs, reports, instruments, and market bars is implemented and documented as verified.
- Phase 2B: provider sync, Polygon provider boundary, scheduler, sync audit, readiness gates, guarded smoke commands, and frontend sync visibility are documented as complete; legacy sample-provider behavior has been removed from runtime paths.
- Phase 2C: option contracts, option snapshots, option-chain sync, options APIs, selected contract bars API, and workbench UI slices through slice 27 are implemented in the working tree, with an additional reverse-proxy preview fix recorded in the roadmap.
- Current Phase 5 state: Phase 5 paper-only MVP is implemented and completion-audited. Phase 4 completed the approved research-only Strategy Lab experiment workbench scope. Phase 5 now has paper-only architecture documentation, backend domain contracts, pure RiskGuard evaluator, SQLAlchemy persistence models, SQL schema, repository methods, append-only audit event persistence, human-facing paper intent API endpoints, a local deterministic paper adapter, and a Candidate-to-Paper Strategy Lab UI flow for paper draft creation, RiskGuard review, human approval/rejection, paper submit, and cancellation. Completion verification passed focused paper tests, full backend regression, frontend build, and paper-only safety grep. Live broker execution, broker credentials, broker account mutation, AI-directed live trading, trading-scope MCP tools, network execution, live-trading UI controls, and automatic paper-to-live promotion remain out of scope.
- Current Phase 6 state: Phase 6 paper-only workflow hardening is complete and completion-audited. Phase 6 added and verified a Playwright Chromium browser smoke for the Strategy Lab Candidate-to-Paper UI, a paper account summary API, a paper PnL snapshot API using explicit caller-provided reference prices, and a Strategy Lab paper risk dashboard for cash, equity, PnL, positions, recent paper flow, and audit preview. Completion verification passed focused paper tests, full backend regression, frontend build, browser smoke, and safety grep classification. Live broker execution, broker credentials, broker account mutation, AI-directed live trading, trading-scope MCP tools, live-trading UI controls, and automatic paper-to-live promotion remain out of scope.
- Current Phase 7 state: Phase 7 real TradingAgents research execution integration is complete for the approved scope. Slice 1 documented the roadmap and execution boundary. Slice 2 added a typed backend TradingAgents adapter contract that maps existing analysis requests into normalized research execution input, maps completed adapter output into the existing report schema, and sanitizes provider/runtime errors into progress events. Slice 3 connected `start_analysis` to a deterministic local research runner fixture through that adapter boundary, so the analysis API can now persist completed Chinese-first reports without external provider calls. Slice 4 added a runtime-gated real TradingAgents runner path and non-secret AI runtime settings while keeping deterministic execution as the default. Slice 5 improved Analysis and Runs UI observability for completed reports and failed/no-report states. Slice 6 completion-audited Phase 7 with backend full regression, frontend build, browser smoke, and safety grep classification. A controlled fixture failure path still persists failed/no-report runs. Live broker execution, broker credentials, broker account mutation, AI-directed live trading, trading-scope MCP tools, live-trading UI controls, and automatic paper-to-live promotion remain out of scope.
- Current Phase 8 state: Phase 8 research operations hardening is underway. Slice 1 documented the roadmap and operations boundary. Slice 2 exposed persisted `AQUANTLENS_TRADINGAGENTS_*` runner settings in the Settings model/agent UX, including runner mode, provider, quick/deep models, output language, selected analysts, and debate rounds. Slice 3 added a guarded manual real-runner smoke CLI and wrapper that require explicit real-runner mode, an operator confirmation flag, and provider readiness before invoking TradingAgents. Deterministic mode remains the default. Provider-backed research remains opt-in behind an explicit runtime gate. Live broker execution, broker credentials, broker account mutation, AI-directed live trading, trading-scope MCP tools, live-trading UI controls, and automatic paper-to-live promotion remain out of scope.
- The checked-in analysis endpoint no longer emits sample or mock research reports. Until the real TradingAgents execution chain is connected in Slice 4, deterministic fixture reports are used only to verify the analysis execution, report mapping, and persistence path.
- Runtime DB hygiene is documented in `docs/operations/runtime-db-hygiene.md`; pytest defaults to a temporary SQLite database and the cleanup script backs up before removing mock/test/legacy task rows.

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
- `docs/architecture/agent-gateway-and-strategy-lab.md`
- `docs/roadmap/phase-2a-roadmap.md`
- `docs/roadmap/phase-2a-verification.md`
- `docs/roadmap/phase-2b-roadmap.md`
- `docs/roadmap/phase-2b-completion-audit.md`
- `docs/roadmap/phase-2c-roadmap.md`
- `docs/roadmap/phase-2c-completion-audit.md`
- `docs/roadmap/phase-2d-roadmap.md`
- `docs/roadmap/phase-2d-completion-audit.md`
- `docs/roadmap/phase-3-roadmap.md`
- `docs/roadmap/phase-3-completion-audit.md`
- `docs/roadmap/phase-4-roadmap.md`
- `docs/roadmap/phase-4-completion-audit.md`
- `docs/roadmap/phase-5-roadmap.md`
- `docs/roadmap/phase-5-completion-audit.md`
- `docs/roadmap/phase-6-roadmap.md`
- `docs/roadmap/phase-6-completion-audit.md`
- `docs/roadmap/phase-7-roadmap.md`
- `docs/roadmap/phase-7-completion-audit.md`
- `docs/roadmap/phase-8-roadmap.md`
- `docs/superpowers/specs/2026-06-20-aquantlens-us-phase-5-paper-only-design.md`
- `docs/superpowers/plans/2026-06-20-aquantlens-us-phase-5-slice-2-paper-contracts.md`
- `docs/superpowers/plans/2026-06-20-aquantlens-us-phase-5-slice-3-riskguard.md`
- `docs/superpowers/plans/2026-06-20-aquantlens-us-phase-5-slice-4-paper-persistence-audit.md`
- `docs/superpowers/plans/2026-06-20-aquantlens-us-phase-5-slice-5-paper-intent-api.md`
- `docs/superpowers/plans/2026-06-20-aquantlens-us-phase-5-slice-6-paper-adapter-simulation.md`
- `docs/superpowers/plans/2026-06-20-aquantlens-us-phase-5-slice-7-candidate-to-paper-ui.md`
- `docs/superpowers/plans/2026-06-20-aquantlens-us-phase-6-slice-1-roadmap.md`
- `docs/superpowers/plans/2026-06-20-aquantlens-us-phase-6-slice-2-paper-workflow-browser-smoke.md`
- `docs/superpowers/plans/2026-06-20-aquantlens-us-phase-6-slice-3-paper-account-summary-api.md`
- `docs/superpowers/plans/2026-06-20-aquantlens-us-phase-6-slice-4-paper-pnl-snapshot.md`
- `docs/superpowers/plans/2026-06-20-aquantlens-us-phase-6-slice-5-paper-risk-dashboard-ui.md`
- `docs/superpowers/plans/2026-06-20-aquantlens-us-phase-6-slice-6-completion-audit.md`
- `docs/superpowers/plans/2026-06-20-aquantlens-us-phase-7-slice-1-roadmap.md`
- `docs/superpowers/plans/2026-06-20-aquantlens-us-phase-7-slice-2-adapter-contract.md`
- `docs/superpowers/plans/2026-06-20-aquantlens-us-phase-7-slice-3-deterministic-runner.md`
- `docs/superpowers/plans/2026-06-20-aquantlens-us-phase-7-slice-4-real-runner-gate.md`
- `docs/superpowers/plans/2026-06-20-aquantlens-us-phase-7-slice-5-observability-ui.md`
- `docs/superpowers/plans/2026-06-20-aquantlens-us-phase-7-slice-6-completion-audit.md`
- `docs/superpowers/plans/2026-06-20-aquantlens-us-phase-8-slice-1-roadmap.md`
- `docs/superpowers/plans/2026-06-20-aquantlens-us-phase-8-slice-2-runner-settings-ux.md`
- `docs/superpowers/specs/2026-06-17-aquantlens-phase-1-design.md`
- `docs/superpowers/plans/2026-06-17-aquantlens-phase-1.md`
