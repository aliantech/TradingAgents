# Phase 9 Slice 3 Report Review Contract Plan

**Goal:** Add a lightweight operator review contract for completed research reports while preserving the research-only boundary.

## Tasks

- [x] Add report review persistence through the existing database boundary.
- [x] Add review dimensions for evidence clarity, consistency, risk coverage, options relevance, Chinese readability, and research-only safety.
- [x] Add free-text reviewer notes.
- [x] Add report review create/list APIs under report resources.
- [x] Add focused backend tests for repository and API behavior.

## Verification

- Focused backend tests cover creating and listing reviews: 13 passed on Ubuntu temporary copy `/tmp/tradingagents-phase9-slice3-verify-FOgugO`.
- Backend full regression passed on the same Ubuntu temporary copy: 261 passed.
- Existing report APIs still pass.
- The contract does not score investment correctness or grant trading authority.

## Non-Goals

- No provider calls.
- No automated investment correctness scoring.
- No broker integration.
- No live execution.
- No paper-to-live workflow.
- No UI changes in this slice.
