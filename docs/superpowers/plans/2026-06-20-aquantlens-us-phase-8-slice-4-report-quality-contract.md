# Phase 8 Slice 4 Report Quality Contract Plan

**Goal:** Add a lightweight report-quality validation layer for Chinese-first research reports before they are persisted.

**Scope:** Backend report quality checks, adapter integration, focused tests, roadmap and project documentation. The checks validate product structure and safety language, not investment correctness.

## Tasks

- [x] Add a report quality module for Chinese-first structural checks.
- [x] Require non-empty report sections with Chinese text for `zh` reports.
- [x] Require evidence labels and risk factors.
- [x] Require confidence bounds through the existing schema and contract check.
- [x] Require research-only or no-trading-authority language in plan/risk sections.
- [x] Invoke the contract before `TradingAgentsRunResult` is mapped into a persisted `ResearchReport`.
- [x] Persist invalid mapped reports as failed/no-report runs with a `report_quality` progress event.
- [x] Add focused backend tests for valid and invalid report payloads.

## Verification

- Ubuntu temp copy focused tests:
  - `tests/test_report_quality.py`
  - `tests/test_tradingagents_adapter.py`
  - `tests/test_analysis_api_persistence.py`
  - `tests/test_tradingagents_runner.py`
- Existing analysis API tests still pass.
- No provider calls are required.

## Non-Goals

- No investment-correctness scoring.
- No LLM-as-judge report review.
- No broker integration.
- No live execution or paper-to-live workflow.
