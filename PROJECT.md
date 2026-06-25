# AQuantLens US Options Branch

## Status

Status: Phase 13 Option Chain Readiness Gate Complete
Last Reviewed: 2026-06-24
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
- Phase 2B historical sync work is superseded: direct Polygon/Massive market-data API calls, provider sync commands, scheduler, and guarded live-smoke scripts have been removed from this project. Finance Data Hub is now the data-source owner.
- Phase 2C option contracts, option snapshots, options APIs, selected contract bars API, and workbench UI remain as research/workbench consumers. Option-chain and bars reads should come from Finance Data Hub first, with local persisted rows treated as read-only fallback/history.
- Current Phase 5 state: Phase 5 paper-only MVP is implemented and completion-audited. Phase 4 completed the approved research-only Strategy Lab experiment workbench scope. Phase 5 now has paper-only architecture documentation, backend domain contracts, pure RiskGuard evaluator, SQLAlchemy persistence models, SQL schema, repository methods, append-only audit event persistence, human-facing paper intent API endpoints, a local deterministic paper adapter, and a Candidate-to-Paper Strategy Lab UI flow for paper draft creation, RiskGuard review, human approval/rejection, paper submit, and cancellation. Completion verification passed focused paper tests, full backend regression, frontend build, and paper-only safety grep. Live broker execution, broker credentials, broker account mutation, AI-directed live trading, trading-scope MCP tools, network execution, live-trading UI controls, and automatic paper-to-live promotion remain out of scope.
- Current Phase 6 state: Phase 6 paper-only workflow hardening is complete and completion-audited. Phase 6 added and verified a Playwright Chromium browser smoke for the Strategy Lab Candidate-to-Paper UI, a paper account summary API, a paper PnL snapshot API using explicit caller-provided reference prices, and a Strategy Lab paper risk dashboard for cash, equity, PnL, positions, recent paper flow, and audit preview. Completion verification passed focused paper tests, full backend regression, frontend build, browser smoke, and safety grep classification. Live broker execution, broker credentials, broker account mutation, AI-directed live trading, trading-scope MCP tools, live-trading UI controls, and automatic paper-to-live promotion remain out of scope.
- Current Phase 7 state: Phase 7 real TradingAgents research execution integration is complete for the approved scope. Slice 1 documented the roadmap and execution boundary. Slice 2 added a typed backend TradingAgents adapter contract that maps existing analysis requests into normalized research execution input, maps completed adapter output into the existing report schema, and sanitizes provider/runtime errors into progress events. Slice 3 connected `start_analysis` to a deterministic local research runner fixture through that adapter boundary, so the analysis API can now persist completed Chinese-first reports without external provider calls. Slice 4 added a runtime-gated real TradingAgents runner path and non-secret AI runtime settings while keeping deterministic execution as the default. Slice 5 improved Analysis and Runs UI observability for completed reports and failed/no-report states. Slice 6 completion-audited Phase 7 with backend full regression, frontend build, browser smoke, and safety grep classification. A controlled fixture failure path still persists failed/no-report runs. Live broker execution, broker credentials, broker account mutation, AI-directed live trading, trading-scope MCP tools, live-trading UI controls, and automatic paper-to-live promotion remain out of scope.
- Current Phase 8 state: Phase 8 research operations hardening is complete and completion-audited. Slice 1 documented the roadmap and operations boundary. Slice 2 exposed persisted `AQUANTLENS_TRADINGAGENTS_*` runner settings in the Settings model/agent UX, including runner mode, provider, quick/deep models, output language, selected analysts, and debate rounds. Slice 3 added a guarded manual real-runner smoke CLI and wrapper that require explicit real-runner mode, an operator confirmation flag, and provider readiness before invoking TradingAgents. Slice 4 added a lightweight report-quality contract for Chinese-first sections, evidence labels, confidence bounds, and no-trading-authority language before report persistence. Slice 5 added normalized failed-run diagnostics for provider/model/runtime/report-quality errors and surfaced category, failed step, sanitized message, and retry guidance in Runs. Slice 6 audited Phase 8 with focused backend tests, full backend regression, frontend build, browser smoke, and safety grep classification. Deterministic mode remains the default. Provider-backed research remains opt-in behind an explicit runtime gate. Live broker execution, broker credentials, broker account mutation, AI-directed live trading, trading-scope MCP tools, live-trading UI controls, scheduled provider-backed research jobs, automatic retry loops, and automatic paper-to-live promotion remain out of scope.
- Current Phase 9 state: Phase 9 research evaluation is complete and completion-audited. Slice 1 defined the roadmap for repeatable evaluation cases, report review contracts, review UI, and a manual provider pilot SOP. Slice 2 added a small versioned research evaluation case set covering SPY, QQQ, AAPL, TSLA, and SPX with deterministic baseline request generation and focused backend validation tests. Slice 3 added report review persistence and report review create/list APIs for evidence clarity, consistency, risk coverage, options relevance, Chinese readability, research-only safety, and reviewer notes. Slice 4 exposed report review status, latest notes, score summary, and a compact operator review form in the Reports workbench, plus review context in Runs detail. Slice 5 documented the manual provider pilot SOP using the Phase 8 guarded smoke path and records only non-secret metadata, quality notes, and residual risks. Slice 6 audited Phase 9 with focused backend tests, full backend regression, frontend build, browser smoke, and safety grep classification. Real provider-backed research remains manual and opt-in behind explicit runtime gates. Live broker execution, broker credentials, broker account mutation, AI-directed live trading, trading-scope MCP tools, live-trading UI controls, scheduled provider-backed research jobs, automatic retry loops, and automatic paper-to-live promotion remain out of scope.
- Current Phase 10 state: Phase 10 manual provider pilot is complete with a pause decision. Slice 1 defined the SPY-first manual pilot roadmap and checklist. Slice 2 generated and recorded the SPY deterministic baseline review through the existing deterministic analysis and report review paths. Slice 3 executed the approved guarded real-runner wrapper for SPY and recorded a sanitized `not_ready` result because `OPENAI_API_KEY` was missing from the operator process. Slice 4 decided to pause for provider readiness, then repeat `SPY` instead of expanding to `QQQ`. Slice 5 was skipped. Slice 6 audited completion and residual risks. No runtime code, real provider call, broker integration, live execution, scheduled job, automatic retry, or paper-to-live workflow was added in Phase 10.
- Current Phase 11 state: Phase 11 repeat-SPY smoke is complete with a market-data runtime failure decision. Slice 1 defined the roadmap and checklist for confirming provider readiness without exposing secret values, then repeating the approved guarded SPY smoke before any QQQ expansion. Slice 2 first recorded `not_ready`, then fixed the Settings-saved LLM key bridge so the guarded smoke CLI can use write-only Settings secrets without printing them; masked Settings API readback confirmed `OPENAI_API_KEY` is saved and final readiness was `ready`. Slice 3 installed TradingAgents real-runner dependencies into the Ubuntu backend venv, executed the approved wrapper for SPY, and recorded a sanitized `failed` result because the Yahoo/yfinance market-data path failed SSL hostname validation before report generation. Slice 4 was skipped because no report was generated. Slice 5 decided to fix the real-runner market-data SSL/runtime path, then repeat `SPY`; do not expand to `QQQ` yet. Slice 6 audited completion and residual risks. Live broker execution, broker credentials, broker account mutation, AI-directed live trading, trading-scope MCP tools, live-trading UI controls, scheduled provider-backed research jobs, automatic retry loops, and automatic paper-to-live promotion remain out of scope.
- Current Phase 12 state: Phase 12 is complete with a fix-before-expansion decision. Slice 1 added a minimal direct Yahoo Finance chart endpoint vendor for core OHLCV data, registered it as `direct_yahoo_chart`, configured the real TradingAgents runner to use it for `get_stock_data`, and then extended technical-indicator OHLCV to use the same direct chart path after the first repeated smoke exposed the remaining yfinance `fc.yahoo.com` dependency. Slice 2 added an explicit `macro_unavailable` vendor for manual smoke runs without `FRED_API_KEY`, then repeated the approved guarded `SPY` smoke successfully. Slice 3 persisted and reviewed the first provider-backed SPY report. The review failed expansion readiness because the report stated `SPY` close `746.74` for `2026-06-18` while the direct Yahoo chart validation returned `549.33` for the same date. Decision: do not expand to `QQQ`; fix SPY report data-grounding and residual yfinance outcome-resolution warnings first. Live broker execution, broker credentials, broker account mutation, AI-directed live trading, trading-scope MCP tools, live-trading UI controls, scheduled provider-backed research jobs, automatic retry loops, and automatic paper-to-live promotion remain out of scope.
- Current Phase 13 state: Phase 13 Slice 1 implemented the real-runner data-grounding gate. Real-runner mapped reports now include the deterministic direct Yahoo chart verified market-data snapshot in market/technical report sections and markdown, add evidence label `direct-yahoo-chart-verified-snapshot`, and fail report quality if same-date close claims conflict with the verified snapshot close. Slice 2 repeated the provider-backed `SPY` persisted analysis in an isolated Ubuntu copy and created a review. The new report's snapshot and the current direct Yahoo chart endpoint both returned `SPY` close `746.74` for `2026-06-18`, so the Phase 12 `549.33` comparison is no longer reproducible against the current endpoint. Slice 3 changed deferred reflection outcome resolution from yfinance `Ticker.history()` to the direct Yahoo chart frame path and passed focused/broader unit regressions. Slice 4 added a bounded non-LLM runtime probe that blocks `yfinance.Ticker`, emits JSON, and returned `status=succeeded` for `SPY 2026-06-18`. Slice 5 repeated the full guarded `SPY` real-runner path; smoke exited `0`, stderr was empty, `fc.yahoo.com` count was `0`, and the persisted report completed with no close conflict. Slice 6 improved mapped real-runner report output so one-word final decisions become research-only plans and options observation becomes a concrete risk checklist instead of placeholder text. Slice 7 repeated the guarded provider-backed `SPY` path with the improved mapping; smoke exited `0`, persisted report completed, old mapping placeholders were absent, and review improved risk coverage to `4` and options relevance to `3`. Slice 8 connected persisted option-chain snapshots into real-runner report mapping; `QQQ` currently has persisted option snapshots in the runtime DB, while `SPY` currently does not. Slice 9 added an explicit option-chain readiness gate for guarded real-runner smoke runs; with the gate enabled, SPY is blocked before provider execution when no persisted option-chain context exists. Do not run `QQQ` or another provider-backed path automatically yet; next choose between a guarded QQQ pilot with the gate enabled or first syncing SPY option-chain snapshots and repeating SPY.
- Current provider-boundary update: real-runner market OHLCV, technical-indicator OHLCV, verified market snapshots, and deferred outcome return resolution now read market bars from Finance Data Hub. The old direct Yahoo chart vendor was removed from the active dataflow registry and source file. Historical Phase 12/13 documents still describe the earlier direct-Yahoo mitigation as archival evidence only.
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
- `docs/roadmap/phase-8-completion-audit.md`
- `docs/roadmap/phase-9-roadmap.md`
- `docs/roadmap/phase-9-completion-audit.md`
- `docs/roadmap/phase-10-roadmap.md`
- `docs/roadmap/phase-11-roadmap.md`
- `docs/roadmap/phase-12-roadmap.md`
- `docs/roadmap/phase-13-roadmap.md`
- `docs/operations/phase-9-evaluation-cases.md`
- `docs/operations/phase-9-manual-provider-pilot.md`
- `docs/operations/phase-10-first-pilot-checklist.md`
- `docs/operations/phase-10-spy-deterministic-baseline-review.md`
- `docs/operations/phase-10-spy-real-runner-smoke.md`
- `docs/operations/phase-10-first-case-decision-record.md`
- `docs/roadmap/phase-10-completion-audit.md`
- `docs/operations/phase-11-repeat-spy-readiness-checklist.md`
- `docs/operations/phase-11-provider-readiness-check.md`
- `docs/operations/phase-11-settings-key-readiness-bridge.md`
- `docs/operations/phase-11-spy-repeat-real-runner-smoke.md`
- `docs/operations/phase-11-decision-record.md`
- `docs/roadmap/phase-11-completion-audit.md`
- `docs/operations/phase-12-direct-yahoo-chart-validation.md`
- `docs/operations/phase-12-spy-real-runner-smoke.md`
- `docs/operations/phase-12-spy-provider-report-review.md`
- `docs/operations/phase-13-spy-data-grounding-gate.md`
- `docs/operations/phase-13-spy-repeat-provider-review.md`
- `docs/operations/phase-13-outcome-resolution-direct-chart.md`
- `docs/operations/phase-13-outcome-resolution-runtime-probe.md`
- `docs/operations/phase-13-full-spy-provider-review.md`
- `docs/operations/phase-13-report-mapping-improvement.md`
- `docs/operations/phase-13-spy-mapping-provider-review.md`
- `docs/operations/phase-13-option-chain-context.md`
- `docs/operations/phase-13-option-chain-readiness-gate.md`
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
- `docs/superpowers/plans/2026-06-20-aquantlens-us-phase-8-slice-3-real-runner-smoke.md`
- `docs/superpowers/plans/2026-06-20-aquantlens-us-phase-8-slice-4-report-quality-contract.md`
- `docs/superpowers/plans/2026-06-20-aquantlens-us-phase-8-slice-5-runner-failure-diagnostics.md`
- `docs/superpowers/plans/2026-06-20-aquantlens-us-phase-8-slice-6-completion-audit.md`
- `docs/superpowers/plans/2026-06-20-aquantlens-us-phase-9-slice-1-roadmap.md`
- `docs/superpowers/plans/2026-06-20-aquantlens-us-phase-9-slice-2-evaluation-case-set.md`
- `docs/superpowers/plans/2026-06-20-aquantlens-us-phase-9-slice-3-report-review-contract.md`
- `docs/superpowers/plans/2026-06-20-aquantlens-us-phase-9-slice-4-review-ui.md`
- `docs/superpowers/plans/2026-06-20-aquantlens-us-phase-9-slice-5-manual-provider-pilot-sop.md`
- `docs/superpowers/plans/2026-06-20-aquantlens-us-phase-10-slice-1-roadmap.md`
- `docs/superpowers/plans/2026-06-20-aquantlens-us-phase-10-slice-2-deterministic-baseline-review.md`
- `docs/superpowers/plans/2026-06-20-aquantlens-us-phase-10-slice-3-real-runner-smoke.md`
- `docs/superpowers/plans/2026-06-20-aquantlens-us-phase-10-slice-4-decision-record.md`
- `docs/superpowers/plans/2026-06-20-aquantlens-us-phase-10-slice-6-completion-audit.md`
- `docs/superpowers/plans/2026-06-20-aquantlens-us-phase-11-slice-1-roadmap.md`
- `docs/superpowers/plans/2026-06-20-aquantlens-us-phase-11-slice-2-provider-readiness.md`
- `docs/superpowers/plans/2026-06-20-aquantlens-us-phase-11-slice-3-repeat-spy-smoke.md`
- `docs/superpowers/plans/2026-06-20-aquantlens-us-phase-12-slice-1-direct-yahoo-chart.md`
- `docs/superpowers/specs/2026-06-17-aquantlens-phase-1-design.md`
- `docs/superpowers/plans/2026-06-17-aquantlens-phase-1.md`
