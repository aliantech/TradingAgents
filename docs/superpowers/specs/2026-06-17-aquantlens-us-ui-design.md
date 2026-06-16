# AQuantLens US Options Branch UI Design

## Goal

Define a practical UI direction for the AQuantLens US/options branch that can support the current research and options-data roadmap without copying the existing AQuantLens mainline frontend.

The UI should become a Chinese-first U.S. market research workbench for equities, indices, SPX/SPY/QQQ, and selected liquid U.S. options. It should feel like a focused research terminal: dense, calm, readable, and workflow-oriented.

## Reference Boundary

The existing AQuantLens main project is useful as a workflow reference, not as a direct frontend template.

Borrow from the main project:

- App shell pattern: left navigation, top status/header, main workspace.
- Dashboard decision flow: "what should I research today" instead of generic KPI display.
- Task center model: running, completed, failed, and all analysis runs.
- Report detail model: report metadata, risk notice, summary, module tabs, Markdown and JSON views.
- U.S. option-chain interaction: expiry tabs, moneyness filters, Call/Strike/Put table, selected contract details.

Do not borrow directly:

- Vue 3 and Element Plus implementation.
- Multi-market A-share/HK-stock assumptions.
- Learning Center scope.
- Paper trading or broker execution entry points.
- Large generic admin menus that do not serve Phase 1/2C.

## Product Discipline

Avoid copying the main AQuantLens frontend wholesale. A feature should be added only when it serves a current US/options research workflow or an explicit Phase 1/2C acceptance criterion.

Rules:

- Borrow workflows, not screens.
- Rebuild components in the new React/shadcn system instead of translating Vue files line by line.
- Keep navigation shallow and focused; do not recreate every mainline AQuantLens menu.
- Prefer one strong table or panel over multiple decorative summary cards.
- Do not add "future platform" placeholders that users cannot act on.
- Do not add paper trading, broker actions, learning content, public SaaS pages, billing, or multi-market A-share/HK flows in this branch's MVP.
- When a page starts to require unrelated concepts, split it or defer the extra scope.
- Every Dashboard block must link to a real workflow or expose real readiness/status data.

## Technology Direction

Use the Phase 1 frontend stack:

- React + Vite + TypeScript.
- Tailwind CSS.
- shadcn/ui for app shell, buttons, forms, tabs, dialogs, sheets, command/search, and base table styling.
- TanStack Table for dense option-chain and run/report tables.
- lightweight-charts for market bars, intraday charts, and selected option-contract bars.
- i18next for bilingual UI, with Chinese as the default language.

Tremor dashboard patterns may be used as visual reference for compact KPI cards and status panels, but the implementation should stay inside the local React/shadcn stack unless there is a clear reason to add a dependency.

## Product Shape

The product starts directly in the workbench, not on a landing page.

Primary navigation:

- Dashboard / 研究驾驶舱
- Analysis / AI 分析
- Reports / 研究报告
- Market Data / 行情数据
- Options / 期权链
- Runs / 任务中心
- Settings / 设置

Phase 1 should not add public marketing pages, multi-user SaaS pages, billing, mobile-app flows, or live-trading surfaces.

## App Shell

The app shell should include:

- Fixed left sidebar with collapsible navigation.
- Sticky top header with symbol search, market/session state, provider readiness, and language switch.
- Main content area with a standard width for reports/settings and a wide mode for charts, tables, and option chains.
- Mobile sidebar overlay and responsive table overflow behavior.

The shell should support long-running workflows: users should be able to move between analysis, runs, reports, and options without losing basic context.

## Dashboard

The Dashboard answers: "今天该研究什么?"

Recommended first screen:

- Top command/search: symbol input for SPY, QQQ, SPX, VIX, AAPL, MSFT, NVDA, TSLA, AMZN, META.
- Readiness strip: backend health, provider status, bars coverage, option snapshots, latest sync.
- Market pulse: compact SPY, QQQ, SPX, VIX chart tiles.
- Research queue: running and failed TradingAgents runs that need attention.
- AI findings: recent Chinese report highlights.
- Options watch: selected underlyings with IV, open interest, volume, and nearest expiry status.
- Data readiness: market bars, option contracts, option snapshots, provider sync runs.

Dashboard cards should be useful entry points, not decorative metrics.

## Analysis Page

The Analysis page starts a TradingAgents research run.

Required controls:

- Symbol input with supported-market validation.
- Analysis date.
- Model/provider selector.
- Research depth selector.
- Analyst/team selector mapped to TradingAgents capabilities.
- Start button.
- Progress panel for status, current step, elapsed time, and errors.

The page should emphasize that output is research assistance, not investment advice or live execution.

## Runs Page

The Runs page adapts the AQuantLens task-center model for TradingAgents runs.

Required views:

- Running
- Completed
- Failed
- All

Table columns:

- Run ID
- Symbol
- Market
- Status
- Progress
- Model/provider
- Started at
- Duration
- Actions

Actions:

- Open report for completed runs.
- View progress or logs for running runs.
- View error detail for failed runs.
- Retry failed runs when the backend contract supports retry safely.

Progress updates should use WebSocket or SSE when available. Polling is acceptable as a fallback.

## Reports Page

The Reports page should support both list and detail workflows.

Report list:

- Symbol
- Report title
- Status
- Created time
- Model/provider
- Analyst set
- Tags or source run

Report detail:

- Header with symbol, status, created time, model/provider, and analyst set.
- Fixed risk notice band.
- Executive summary.
- Key points.
- Module tabs for structured report sections.
- Markdown rendering for reader-facing content.
- JSON view for structured data inspection and future search/analytics.
- Download actions for Markdown and JSON first. PDF and DOCX are deferred unless already supported by the backend.

Do not add "apply to trading" or broker-order actions in Phase 1/2C.

## Market Data Page

The Market Data page gives chart and data context around supported symbols.

Required areas:

- Symbol selector.
- Timeframe controls for 1m and 1d bars.
- Candlestick or line chart through lightweight-charts.
- Volume pane.
- Latest data-source and sync status.
- Basic table preview of recent bars.

Future chart markers may show AI report events and generated signal annotations, but drawing tools and TradingView Advanced Charts are deferred.

## Options Page

The Options page is the highest-priority UI surface for Phase 2C.

It should adapt the existing AQuantLens U.S. option-chain interaction into React:

- Underlying selector for SPY, QQQ, SPX, and selected single names.
- Provider/readiness notice.
- Expiry strip with horizontal tabs.
- Moneyness segmented control: 近价, 全部, 价内, 价外.
- Dense Call / Strike / Put table.
- Sticky strike column.
- Underlying price marker near the closest strike.
- Selected contract state.
- Selected contract detail panel with latest quote, IV, Greeks, OI, volume, and contract metadata.
- Selected contract bars panel when option historical bars are available.

Suggested columns:

- Call side: Delta, IV, OI, Volume, Last, Mid, Bid, Ask.
- Center: Strike.
- Put side: Bid, Ask, Mid, Last, Volume, OI, IV, Delta.

If snapshot data is unavailable but contract metadata exists, the UI should show the table with missing quote fields as unavailable and explain that snapshot ingestion is required.

## Settings Page

Settings should remain operational and narrow:

- Provider readiness and safe display of missing configuration names.
- Model defaults.
- Language preference.
- Data-source status.
- Sync status and recent provider sync runs.

The UI must not display secret values, token contents, private keys, browser sessions, or credential caches.

## Visual System

The visual direction should be restrained and data-focused.

Recommended tokens:

- Page background: `#f8fafc`.
- Surface: `#ffffff`.
- Border: `#e2e8f0`.
- Primary text: `#0f172a`.
- Muted text: `#64748b`.
- Primary action: blue family.
- Positive/negative: use one consistent market convention across the app and document it in the frontend constants.
- Border radius: 6-8px for panels and controls.
- Shadows: minimal, mostly 1px borders instead of heavy elevation.

Avoid:

- Marketing hero sections.
- Decorative gradient orbs.
- Nested cards.
- Oversized typography inside dashboards.
- One-note purple/blue gradient styling.
- Generic SaaS feature-card layouts.

## Component Boundaries

Recommended frontend modules:

- `AppShell`: sidebar, header, layout width modes.
- `SymbolSearch`: reusable symbol command/search.
- `ReadinessStrip`: backend/provider/data readiness.
- `MarketPulsePanel`: SPY/QQQ/SPX/VIX chart tiles.
- `AnalysisRunForm`: TradingAgents run creation form.
- `RunProgressPanel`: progress and error display.
- `RunsTable`: TanStack Table for analysis runs.
- `ReportReader`: Markdown/JSON report detail display.
- `MarketChart`: lightweight-charts wrapper for bars.
- `OptionChainTable`: TanStack Table for Call/Strike/Put rows.
- `OptionContractPanel`: selected option contract details and bars.

The option-chain grouping and formatting logic should be kept in utilities so it can be tested without rendering the table.

## Data Flow

The frontend should consume stable API contracts:

- `GET /api/health` or equivalent readiness endpoint.
- `POST /api/analysis/runs`
- `GET /api/analysis/runs`
- `GET /api/analysis/runs/{id}`
- `GET /api/reports`
- `GET /api/reports/{id}`
- `GET /api/market-data/bars`
- `GET /api/options/contracts`
- `GET /api/options/chain`
- `GET /api/provider-sync-runs`

If backend paths differ, the frontend API adapter should hide those differences from components.

## Error and Empty States

Every core page needs explicit states:

- Loading.
- Empty but valid.
- Missing provider readiness.
- Backend unavailable.
- Partial data.
- Failed run or failed sync.

Option-chain empty states should distinguish between:

- Unsupported underlying.
- No contracts.
- Contracts available but no snapshots.
- Provider entitlement or configuration missing.
- Backend/API failure.

## Implementation Priority

Recommended build order:

1. App shell and navigation.
2. Options page skeleton and option-chain table.
3. Runs page and run-status table.
4. Report list and report detail.
5. Market Data chart page.
6. Dashboard composition after underlying modules exist.
7. Settings readiness page.

Dashboard should not be implemented first because it depends on stable data from analysis runs, reports, market data, options, and provider sync status.

Each implementation slice should stay narrow enough to be reviewed independently. A slice is too large if it introduces new navigation, new API adapters, new charting, new report rendering, and new settings behavior at the same time.

## Acceptance Criteria

The UI design is accepted when:

- It uses the React/shadcn stack rather than copying Vue/Element Plus.
- It preserves useful AQuantLens workflow ideas without inheriting A-share or paper-trading scope.
- The Options page can show selected underlyings, expiries, moneyness filters, a Call/Strike/Put table, and selected contract details.
- The Runs page can show analysis progress and failure states.
- The Reports page can read Chinese-first Markdown reports and inspect JSON.
- The Dashboard is composed from real module summaries instead of decorative placeholder metrics.
- No live trading or broker execution surface is introduced.
