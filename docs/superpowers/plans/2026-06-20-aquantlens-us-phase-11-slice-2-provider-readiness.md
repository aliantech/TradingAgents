# Phase 11 Slice 2 Provider Readiness Plan

**Goal:** Check whether the approved wrapper process is ready for a repeat-SPY real-runner smoke without exposing secret values.

## Tasks

- [x] Use an isolated Ubuntu temp copy.
- [x] Enable the explicit real-runner runtime gate in a temporary SQLite database.
- [x] Call the existing readiness guard without running the wrapper.
- [x] Record only status, provider/model names, and missing variable names.

## Verification

- Readiness result recorded as `not_ready`.
- Missing readiness gate recorded as `OPENAI_API_KEY`.
- No `.env` file was sourced.
- No secret value was read, printed, copied, pasted, stored, or committed.
- No wrapper run occurred.
- No provider request was made.

## Non-Goals

- No wrapper execution before readiness is confirmed.
- No provider calls.
- No secret reads or prints.
- No QQQ run.
- No broker integration.
- No live execution.
- No scheduled jobs.
- No automatic retries.
- No paper-to-live workflow.
