# Phase 9 Slice 4 Review UI Plan

**Goal:** Expose report review context in the Reports and Runs views without provider calls.

## Tasks

- [x] Add frontend API types and client functions for report reviews.
- [x] Show review status, latest note, and score summary in the report workbench.
- [x] Add a compact operator review form for completed reports.
- [x] Show report review context in analysis run detail when a run has a report.
- [x] Add mocked browser smoke coverage for saving and viewing a review.

## Verification

- Frontend build passed on Ubuntu temporary copy `/tmp/tradingagents-phase9-slice4-verify-Hq3ccd`.
- Mocked report review browser smoke passed on the same Ubuntu temporary copy: 1 passed.
- Existing analysis observability browser smoke passed on the same Ubuntu temporary copy: 1 passed.
- Focused backend report review tests passed on the same Ubuntu temporary copy: 4 passed.
- Browser tests mock APIs and do not make provider calls.

## Non-Goals

- No provider calls.
- No broker integration.
- No live execution.
- No automatic retries.
- No paper-to-live workflow.
