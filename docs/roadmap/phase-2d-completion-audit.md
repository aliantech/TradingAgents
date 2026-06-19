# Phase 2D Completion Audit

## Status

Status: Complete and validated
Last Reviewed: 2026-06-19
Owner: Yasin

## Summary

Phase 2D turned the AQuantLens US/options branch from a data and configuration workbench into a usable Chinese-first research workflow.

The completed workflow is:

```text
Select symbol
-> review market/options/provider context
-> prepare a research brief
-> choose research template
-> launch TradingAgents analysis
-> read Chinese report with evidence labels
-> compare against prior same-symbol report
-> retry failed runs safely when needed
```

Phase 2D stayed inside the approved research-only boundary. It did not add broker order placement, live execution, AI trading authority, investment-advice positioning, or public SaaS behavior.

## Completed Slices

### Slice 1: Research Brief

Implemented:

- Analysis page shows a pre-run research task brief.
- Brief summarizes symbol, analysis date, model, depth, analyst set, market data, options context, provider readiness, and prior report availability.
- Missing context items link to Market Data, Options, Settings, or Reports.

### Slice 2: Persistent Watchlist

Implemented:

- Dashboard reads and writes `research.watchlist` through database-backed settings.
- Watchlist changes are constrained to supported Phase 1 U.S./index/ETF symbols.
- Settings catalog exposes the watchlist under user/workspace preferences.

### Slice 3: Report Comparison

Implemented:

- `GET /api/reports/{report_id}/comparison`.
- Compares selected report against the prior same-symbol report.
- Returns current/previous report metadata, confidence delta, risk-factor additions/removals, and section-level changed flags.
- Reports UI displays a compact comparison card.

### Slice 4: Research Templates

Implemented:

- `AnalysisRequest.research_template`.
- Supported values: `general`, `earnings-preview`, `macro-options-readthrough`, `technical-setup`.
- `analysis_runs`, analysis run list items, report list items, and `ResearchReport` persist template metadata.
- Analysis UI exposes the template selector and Research Brief displays the selected task type.

### Slice 5: Report Evidence Labels

Implemented:

- `ResearchReport.evidence_labels`.
- Persisted real report labels are supported by schema and UI.
- The checked-in analysis path no longer generates sample reports or sample evidence labels.
- Reports UI displays evidence labels as badges.

### Slice 6: Safe Retry Flow

Implemented:

- `POST /api/analysis/{analysis_id}/retry`.
- Only failed analysis runs can be retried.
- Retry creates a new run from the original request and preserves the failed run as history.
- Runs UI displays `Retry` for failed analysis runs.

## Validation Evidence

Latest Ubuntu backend verification:

```bash
cd /home/yasin/workspace/TradingAgents/backend
. .venv/bin/activate
pytest -q tests/test_analysis_retry_api.py tests/test_analysis_api_persistence.py tests/test_report_comparison_api.py tests/test_analysis_repository.py
```

Result:

```text
11 passed in 1.15s
```

Latest Ubuntu frontend verification:

```bash
cd /home/yasin/workspace/TradingAgents/frontend
npm run build
```

Result:

```text
1927 modules transformed
built in 463ms
```

## Safety Review

Confirmed:

- No live broker order placement was added.
- No AI-direct trading authority was added.
- No broker credentials, API keys, tokens, private keys, or `.env` values were read, printed, copied, or documented.
- Provider secrets remain write-only through settings behavior.
- Phase 2D UI copy remains research-oriented and does not imply investment advice or execution.
- Retry preserves failed runs instead of overwriting historical state.
- QuantDinger was used only as a capability reference; no code or product shell was imported.

## Remaining Risks

- Analysis execution is still synchronous/sample-like underneath the current FastAPI service wrapper; Phase 3 should introduce a durable async job contract before heavier agent or backtest tasks.
- Report evidence labels are currently coarse labels, not source-level citations or confidence scoring.
- Report comparison uses section equality and risk-factor set differences; deeper semantic comparison can come later.
- Local database migrations are lightweight compatibility guards, not a full Alembic migration strategy.
- The frontend retry action does not yet show a dedicated success toast or link directly to the retried run detail.

## Phase 3 Entry Recommendation

Phase 3 should begin with architecture and low-risk research automation rather than trading:

1. Research Agent Gateway design and schema:
   - machine tokens separate from human sessions
   - read/research scopes only
   - audit log
   - rate limits
   - market and instrument allowlists

2. Async job contract:
   - submit
   - poll status
   - retrieve progress/events
   - retrieve result
   - preserve idempotency for writeful agent actions

3. MCP thin wrapper:
   - only over `/api/agent/v1`
   - no direct database reads
   - no broker credentials
   - no trading tools

4. SignalStrategy research lab plan:
   - dataframe signal research
   - deterministic backtest contract
   - chart overlays
   - report-linked strategy notes

Live execution, broker adapters, and paper trading automation should remain out of scope until the research Agent Gateway, async job model, audit log, and risk guard designs are complete.
