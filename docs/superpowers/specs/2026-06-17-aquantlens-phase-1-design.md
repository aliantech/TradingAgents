# AQuantLens US Options Branch Phase 1 Design

## Goal

Build the first U.S.-market AQuantLens branch MVP on top of TradingAgents: a bilingual AI research workbench that generates Chinese-first financial reports, stores U.S. equity/index/options data, and displays basic market charts.

## Background

The current repository is the upstream TradingAgents framework. Yasin Brain already records the official product as AQuantLens, an AI Trading Research Platform. The existing AQuantLens main project has broader market scope and A-share-oriented assumptions, so this design treats the current branch as a separate U.S/options-focused product direction.

## Branch Boundary

- Branch: `aquanlens-us`.
- Role: sibling U.S/options branch under the AQuantLens umbrella.
- Reason: avoid forcing U.S. options workflows into the existing AQuantLens mainline.
- Long-term merge policy: share reusable concepts only after interfaces are stable; do not assume direct code merge.

## Scope

Phase 1 includes:

- API wrapper around TradingAgents.
- React/Vite/TypeScript frontend.
- Chinese-first structured report output.
- PostgreSQL + TimescaleDB persistent storage.
- Redis realtime cache.
- U.S. equities, indices, SPX/SPY/QQQ options, and selected liquid U.S. equity options.
- Basic K-line, intraday, volume, indicator, report marker, and AI signal marker charting via lightweight-charts.

Phase 1 excludes:

- Live broker execution.
- Full backtesting engine.
- Full TradingView proprietary charting.
- Full OPRA tick/quote history.
- Multi-user SaaS, billing, and mobile app work.

## Architecture

Use a separated frontend/backend architecture:

```text
React/Vite UI
-> FastAPI API
-> TradingAgents wrapper
-> PostgreSQL/TimescaleDB
-> Redis
-> ingestion workers
```

The backend owns analysis jobs, report persistence, data normalization, and realtime progress. The frontend owns user workflow, bilingual UI, chart display, and report reading.

## Frontend Design

Use React + Vite + TypeScript with shadcn/ui and Tailwind. Default language is Chinese; English can be selected with i18next.

Primary screens:

- Dashboard
- Analysis
- Reports
- Market Data
- Options
- Settings

The UI should feel like a dense but calm trading research workbench, not a marketing site. It should favor tables, sidebars, charts, filters, and readable reports.

## Backend Design

FastAPI provides stable API contracts:

- Start analysis job.
- Get analysis job status.
- Stream progress through SSE or WebSocket.
- Fetch report by ID.
- List reports.
- Fetch market bars.
- Fetch option-chain snapshots.
- Fetch system/provider settings.

TradingAgents should be wrapped behind a service boundary so upstream code can remain understandable and easier to update.

## Data Design

PostgreSQL + TimescaleDB stores durable data:

- Instruments
- Market bars
- Option contracts
- Option snapshots
- Analysis runs
- Analysis reports
- Provider sync runs

Redis stores realtime and short-lived state:

- Latest quotes
- Job progress
- Option-chain cache
- Market event stream
- Signal stream

Data sources must be abstracted behind provider interfaces. Polygon/Massive, ThetaData, Tradier, and IBKR are likely candidates, but Phase 1 should not hard-code the product to one vendor.

## Report Design

Reports are Chinese-first and structured. Save both Markdown and JSON.

Required report sections:

- 摘要
- 市场背景
- 基本面分析
- 技术面分析
- 情绪面分析
- 期权市场观察
- 多头观点
- 空头观点
- 风险因素
- 交易计划
- 仓位建议
- 止盈止损
- 置信度

Professional terms may remain English or mixed with Chinese.

## Chart Design

Use lightweight-charts in Phase 1.

Supported chart functions:

- K-line chart
- Intraday line/candle chart
- Volume
- MA/EMA overlays
- AI signal markers
- Report event markers

TradingView Advanced Charts and Trading Platform are deferred until the system has real demand for advanced drawing tools, proprietary indicators, chart trading, or external-user terminal workflows.

## Risk and Safety

Phase 1 is research-only. AI output cannot place live orders. The design must make this visible in code and UI language.

Any future automated trading requires a separate risk engine, paper trading phase, broker adapter, audit log, and kill switch.

## Acceptance Criteria

Phase 1 is accepted when:

- The frontend can start an analysis for a supported symbol.
- The backend can run TradingAgents through API.
- Progress is visible in the UI.
- A Chinese structured report is generated and saved.
- Report history is visible.
- A basic chart is shown for the analyzed symbol.
- A selected option-chain snapshot is available for supported option underlyings.
- PostgreSQL/TimescaleDB and Redis responsibilities are implemented or stubbed behind clear interfaces.
