# Phase 10 Slice 1 Roadmap Plan

**Goal:** Define Phase 10 as a narrow manual provider pilot and prepare the first SPY pilot checklist while preserving the no-live-trading boundary.

## Tasks

- [x] Add `docs/roadmap/phase-10-roadmap.md`.
- [x] Add `docs/operations/phase-10-first-pilot-checklist.md`.
- [x] Define first pilot success criteria and stop criteria.
- [x] Keep provider-backed research manual and opt-in.
- [x] Update `PROJECT.md` and Yasin Brain log.

## Verification

- Documentation keeps secrets, broker workflows, scheduled jobs, automatic retries, live execution, and paper-to-live promotion out of scope.
- No runtime code is added in Slice 1.
- Safety grep classifies matches as boundary documentation only.

## Non-Goals

- No provider calls.
- No runtime code.
- No broker integration.
- No live execution.
- No scheduled jobs.
- No automatic retries.
- No paper-to-live workflow.
