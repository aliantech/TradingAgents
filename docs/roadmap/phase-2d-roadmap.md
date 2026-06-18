# Phase 2D Roadmap

## Objective

Phase 2D turns the AQuantLens US/options workbench from a data and configuration foundation into a usable research workflow. The goal is a Chinese-first research loop:

```text
Select symbol
-> review market/options/provider context
-> prepare a research brief
-> launch TradingAgents analysis
-> read and compare the generated Chinese report
-> return to market/options context for the next research question
```

Phase 2D remains research-only. It does not add broker order placement, AI trading authority, live execution, or public investment-advice positioning.

## Entry State

Phase 2C delivered the data and UI foundation:

- Analysis, Reports, Market Data, Options, Runs, and Settings routes.
- Repository-backed analysis runs and Chinese reports.
- Market bars, provider sync audit, option contracts, option-chain snapshots, and selected option bars.
- Settings/API provider credential path with write-only secret handling.
- Provider-not-ready actions that guide users back to Settings.

## Slice 1: Research Brief

Status: implemented in the working tree.

Purpose:

- Make the Analysis page behave like a research launchpad instead of a raw form.
- Convert existing market/options/provider/report state into an explicit pre-run brief.
- Keep the launch flow grounded in real data availability and safe readiness gates.

Implemented surface:

- `ResearchContextCard` shows a Phase 2D research task brief for the current symbol.
- The brief summarizes analysis date, model, depth, analyst set, and launch context readiness.
- Checklist items cover market data, options context, provider readiness, and prior report availability.
- Missing context items expose direct actions to Market Data, Options, Settings, or Reports.

## Next Slices

- Watchlist and research queue: define a small saved symbol list and research priority view.
- Report comparison: compare latest report against prior report for the same symbol.
- Research templates: add task types such as earnings preview, macro/options read-through, and technical setup.
- Report quality pass: improve generated Chinese report structure, evidence labels, and options-specific language.
- Safe retry flow: add retry mutation for failed analysis runs after the backend contract is explicit.

## Verification Targets

- Frontend TypeScript/build passes.
- Backend analysis/report tests remain green.
- No secret values are displayed, logged, or written into docs.
- UI copy stays research-oriented and does not imply broker execution or investment advice.
