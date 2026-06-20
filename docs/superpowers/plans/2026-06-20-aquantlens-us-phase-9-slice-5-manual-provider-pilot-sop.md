# Phase 9 Slice 5 Manual Provider Pilot SOP Plan

**Goal:** Document a safe manual workflow for comparing deterministic and real-runner research outputs without expanding into automation or live trading.

## Tasks

- [x] Add manual provider pilot SOP.
- [x] Tie pilot execution to the Phase 8 guarded real-runner smoke path.
- [x] Define preconditions, allowed metadata, operator steps, stop conditions, and comparison notes.
- [x] Preserve no-secret, no-CI, no-scheduler, no-broker, no-live-execution boundaries.

## Verification

- SOP exists at `docs/operations/phase-9-manual-provider-pilot.md`.
- Safety grep confirms the SOP does not instruct operators to source `.env`, print secrets, or automate provider calls.
- Existing focused tests continue to mock real runner behavior: 16 passed on Ubuntu temporary copy `/tmp/tradingagents-phase9-slice5-verify-b05KPM`.

## Non-Goals

- No provider calls in this slice.
- No runtime code changes.
- No CI or scheduled provider jobs.
- No broker integration.
- No live execution.
- No automatic retry loops.
- No paper-to-live workflow.
