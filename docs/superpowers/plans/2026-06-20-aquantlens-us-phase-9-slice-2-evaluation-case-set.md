# Phase 9 Slice 2 Evaluation Case Set Plan

**Goal:** Define a small, versioned research evaluation case set for repeatable deterministic and manual real-runner comparison.

## Tasks

- [x] Add a backend research evaluation case contract.
- [x] Add five built-in cases covering SPY, QQQ, mega-cap equity, volatile equity, and an index-oriented case.
- [x] Add deterministic baseline request generation.
- [x] Add focused backend tests for validation, coverage, deterministic request generation, and baseline expectations.
- [x] Document operator extension rules.

## Verification

- Focused backend tests validate the case set: 5 passed on Ubuntu temporary copy `/tmp/tradingagents-phase9-slice2-verify-VLZ4Cp`.
- Backend full regression passed on the same Ubuntu temporary copy: 257 passed.
- Documentation explains how operators should extend cases.
- Automated tests do not require provider secrets or live provider calls.

## Non-Goals

- No provider calls.
- No database schema.
- No review storage.
- No UI changes.
- No broker integration.
- No live execution or paper-to-live workflow.
