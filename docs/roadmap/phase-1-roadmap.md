# Phase 1 Roadmap

## Objective

Build the AQuantLens US Options Branch MVP on top of TradingAgents, with bilingual UI, Chinese-first reports, U.S. equity/index/options data foundations, and basic charting.

This roadmap is for a separate U.S.-market branch. It should not inherit A-share assumptions from the existing AQuantLens main project.

## Success Criteria

The phase is complete when the system can run this flow:

```text
User opens the workbench
-> selects SPY, SPX, NVDA, TSLA, or another supported symbol
-> selects model/provider and analysis depth
-> starts a TradingAgents analysis through API
-> watches progress in the frontend
-> receives a Chinese structured report
-> reviews related chart and option-chain context
-> finds the saved report in history
```

## Milestones

### M1: Project Foundation

- Define local project rules and scope.
- Document product identity as an AQuantLens U.S/options branch.
- Keep TradingAgents as the upstream foundation.
- Establish Phase 1 non-goals.

### M2: Backend Service Layer

- Add FastAPI service boundary around TradingAgents.
- Define analysis job API.
- Add structured report schema.
- Add progress streaming contract.
- Save agent run metadata.

### M3: Frontend Workbench

- Build React/Vite/TypeScript app shell.
- Add bilingual UI with Chinese default.
- Add Dashboard, Analysis, Reports, Market Data, Options, and Settings pages.
- Use shadcn/ui and Tailwind for the product UI.

### M4: Data Layer

- Add PostgreSQL + TimescaleDB schema for instruments, bars, options, reports, and runs.
- Add Redis keys/streams for latest quotes, option-chain cache, job progress, and signal events.
- Define market data provider interface.

### M5: Market Data MVP

- Ingest selected U.S. equity, ETF, index, and option data.
- Store 1m and 1d bars.
- Store option contracts and selected option-chain snapshots.
- Avoid full OPRA tick/quote archival in Phase 1.

### M6: Charts and Report Linkage

- Add lightweight-charts for K-line and intraday views.
- Show volume and simple overlays.
- Add report event markers and AI signal markers.
- Link saved reports to symbol/date chart context.

### M7: Phase 1 Verification

- Verify one complete SPY or SPX analysis flow.
- Verify report persistence.
- Verify chart rendering.
- Verify selected option-chain snapshot.
- Verify Redis progress updates.

## Explicit Deferrals

- Live automated trading.
- Full backtesting engine.
- TradingView Advanced Charts or Trading Platform.
- Full drawing tool suite.
- Full OPRA tick/quote history.
- Multi-user auth, billing, and public SaaS features.
