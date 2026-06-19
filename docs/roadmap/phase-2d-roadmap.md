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

Completion audit: `docs/roadmap/phase-2d-completion-audit.md`.

## Entry State

Phase 2C delivered the data and UI foundation:

- Analysis, Reports, Market Data, Options, Runs, and Settings routes.
- Repository-backed analysis runs and Chinese reports.
- Market bars, provider sync audit, option contracts, option-chain snapshots, and selected option bars.
- Settings/API provider credential path with write-only secret handling.
- Provider-not-ready actions that guide users back to Settings.

## Slice 1: Research Brief

Status: implemented and validated on 2026-06-19.

Purpose:

- Make the Analysis page behave like a research launchpad instead of a raw form.
- Convert existing market/options/provider/report state into an explicit pre-run brief.
- Keep the launch flow grounded in real data availability and safe readiness gates.

Implemented surface:

- `ResearchContextCard` shows a Phase 2D research task brief for the current symbol.
- The brief summarizes analysis date, model, depth, analyst set, and launch context readiness.
- Checklist items cover market data, options context, provider readiness, and prior report availability.
- Missing context items expose direct actions to Market Data, Options, Settings, or Reports.

## Slice 2: Persistent Watchlist

Status: implemented and validated on 2026-06-19.

Purpose:

- Turn the Dashboard symbol picker into a saved research watchlist.
- Keep the watchlist in the database-backed settings API instead of local browser state.
- Let users add the active supported symbol to the watchlist or remove symbols while preserving a research-first cockpit.

Implemented surface:

- Dashboard reads `research.watchlist` from `/api/settings`.
- Dashboard writes watchlist changes back to `/api/settings` with `category=user` and `is_secret=false`.
- Settings catalog now exposes `research.watchlist` under user/workspace preferences.
- Watchlist actions are constrained to the currently supported U.S./index/ETF symbol universe.

## Slice 3: Report Comparison

Status: implemented and validated on 2026-06-19.

Purpose:

- Let the research workflow compare the selected report against the prior report for the same symbol.
- Keep the comparison backend-owned so the frontend does not guess history order or diff semantics.
- Surface a compact report delta before future deeper report quality work.

Implemented surface:

- `GET /api/reports/{report_id}/comparison` returns the current report, previous same-symbol report, confidence delta, risk-factor additions/removals, and section-level changed flags.
- Missing prior same-symbol reports return `404` with `previous report not found`.
- Reports UI loads comparison data when a report is selected and shows a compact comparison card with prior summary, confidence delta, changed section count, and risk-factor change counts.

## Slice 4: Research Templates

Status: implemented and validated on 2026-06-19.

Purpose:

- Add task-type intent to the TradingAgents launch contract instead of treating every analysis run as a generic report.
- Support first research templates for general research, earnings preview, macro/options read-through, and technical setup.
- Persist the selected template into run and report metadata so reports can be filtered, compared, and improved by task type later.

Implemented surface:

- `AnalysisRequest` accepts `research_template` with values `general`, `earnings-preview`, `macro-options-readthrough`, and `technical-setup`.
- `analysis_runs` persists `research_template` with lightweight auto-migration for existing local databases.
- `ResearchReport`, report list items, and analysis run list items include `research_template`.
- Generated report Markdown records the selected template.
- Analysis UI exposes a research-template selector and Research Brief displays the selected task type.

## Slice 5: Report Evidence Labels

Status: implemented and validated on 2026-06-19.

Purpose:

- Start the report quality pass by making the evidence basis visible in report JSON, Markdown, and UI.
- Prepare later report improvements such as source confidence, options-specific evidence grouping, and report comparison by evidence class.

Implemented surface:

- `ResearchReport` includes `evidence_labels`.
- Persisted real reports can include evidence labels.
- The checked-in analysis path no longer generates sample reports or sample evidence labels.
- Reports UI displays evidence labels as badges below risk tags.

## Slice 6: Safe Retry Flow

Status: implemented and validated on 2026-06-19.

Purpose:

- Add an explicit retry mutation for failed analysis runs.
- Preserve the original failed run as an audit trail instead of mutating it into a new status.
- Let the Runs page restart a failed research task from the original analysis contract.

Implemented surface:

- `POST /api/analysis/{analysis_id}/retry` creates a new analysis run from the original failed run request.
- Retry returns `409` for non-failed runs.
- Retry returns `404` for unknown analysis IDs.
- Runs UI displays a `Retry` action for failed analysis runs and refreshes analysis/report state after retry.

## Next Slices

- Report quality pass: improve source confidence, options-specific evidence grouping, and Chinese report phrasing.
- Phase 3 planning: research Agent Gateway, async job contract, and SignalStrategy research lab.

## Follow-On Architecture Track

The QuantDinger review produced a separate adoption boundary for future agent and strategy work:

- Reference document: `docs/architecture/agent-gateway-and-strategy-lab.md`.
- Phase 2D remains research-only and should not add broker execution or AI trading authority.
- The first future Agent Gateway should expose only read/research endpoints for market context, options summaries, reports, analysis runs, and async job status.
- The first future MCP server should be a thin wrapper over `/api/agent/v1`, not a direct database or service bypass.
- Strategy Lab should start with dataframe-based signal research before any event-driven paper runtime or broker adapter work.

## Verification Targets

- Frontend TypeScript/build passes.
- Backend analysis/report tests remain green.
- No secret values are displayed, logged, or written into docs.
- UI copy stays research-oriented and does not imply broker execution or investment advice.

## Validation Evidence

Ubuntu runtime validation on 2026-06-19:

```bash
cd /home/yasin/workspace/TradingAgents/frontend
npm run build
```

Result:

```text
1927 modules transformed
built in 467ms
```

```bash
cd /home/yasin/workspace/TradingAgents/backend
. .venv/bin/activate
pytest -q tests/test_analysis_api_persistence.py tests/test_analysis_repository.py
```

Result:

```text
5 passed in 1.07s
```

Slice 2 validation on 2026-06-19:

```bash
cd /home/yasin/workspace/TradingAgents/frontend
npm run build
```

Result:

```text
1927 modules transformed
built in 513ms
```

```bash
cd /home/yasin/workspace/TradingAgents/backend
. .venv/bin/activate
pytest -q tests/test_settings_api.py
```

Result:

```text
1 passed in 0.59s
```

Slice 3 validation on 2026-06-19:

```bash
cd /home/yasin/workspace/TradingAgents/backend
. .venv/bin/activate
pytest -q tests/test_report_comparison_api.py tests/test_analysis_api_persistence.py tests/test_analysis_repository.py
```

Result:

```text
7 passed in 0.98s
```

```bash
cd /home/yasin/workspace/TradingAgents/frontend
npm run build
```

Result:

```text
1927 modules transformed
built in 399ms
```

Slice 4 validation on 2026-06-19:

```bash
cd /home/yasin/workspace/TradingAgents/backend
. .venv/bin/activate
pytest -q tests/test_analysis_api_persistence.py tests/test_report_comparison_api.py tests/test_analysis_repository.py
```

Result:

```text
8 passed in 0.88s
```

```bash
cd /home/yasin/workspace/TradingAgents/frontend
npm run build
```

Result:

```text
1927 modules transformed
built in 522ms
```

Slice 5 validation on 2026-06-19:

```bash
cd /home/yasin/workspace/TradingAgents/backend
. .venv/bin/activate
pytest -q tests/test_analysis_api_persistence.py tests/test_report_comparison_api.py tests/test_analysis_repository.py
```

Result:

```text
9 passed in 0.94s
```

```bash
cd /home/yasin/workspace/TradingAgents/frontend
npm run build
```

Result:

```text
1927 modules transformed
built in 570ms
```

Slice 6 validation on 2026-06-19:

```bash
cd /home/yasin/workspace/TradingAgents/backend
. .venv/bin/activate
pytest -q tests/test_analysis_retry_api.py tests/test_analysis_api_persistence.py tests/test_report_comparison_api.py tests/test_analysis_repository.py
```

Result:

```text
11 passed in 1.12s
```

```bash
cd /home/yasin/workspace/TradingAgents/frontend
npm run build
```

Result:

```text
1927 modules transformed
built in 484ms
```
