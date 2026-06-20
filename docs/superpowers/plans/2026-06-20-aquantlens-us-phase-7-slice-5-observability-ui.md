# Phase 7 Slice 5 Analysis Observability UI Plan

> **For agentic workers:** This slice improves analysis run visibility only. Do not add trading controls or paper-to-live actions.

**Goal:** Make completed reports and failed/no-report analysis states visible from the Analysis page and Runs center.

**Architecture:** Reuse existing analysis status, runs, and reports APIs. The UI displays report links when `report_id` exists, highlights failed/no-report states, and keeps retry explicit from the Runs center.

---

## File Structure

- Modify: `frontend/src/features/analysis/AnalysisPanel.tsx`
  - Show an Open Report action when the current analysis status has a report id.
  - Highlight failed/no-report status with clear copy.
- Modify: `frontend/src/app/App.tsx`
  - Wire Analysis page report opening to the existing report selection flow.
  - Show report id/action and failed/no-report copy in the Runs detail panel.
- Modify: `frontend/src/i18n/index.ts`
  - Add Chinese and English failed/no-report observability copy.
- Create: `frontend/e2e/analysis-observability-smoke.spec.ts`
  - Mock completed and failed analysis API states.
  - Verify completed report opening.
  - Verify failed/no-report progress detail.
- Modify: `docs/roadmap/phase-7-roadmap.md`
  - Mark Slice 5 complete and record verification.
- Modify: `PROJECT.md`
  - Update current Phase 7 status.
- Modify: `/Users/yasin/Documents/Yasin AI OS/04-Projects/aquantlens/LOG.md`
  - Record Slice 5 implementation for the separate US/options branch.

## Safety Boundary

This slice must not add:

- Live-trading UI controls.
- Broker UI controls.
- Trading-scope MCP controls.
- Automatic paper-to-live promotion.
- Provider calls in browser tests.

## Tasks

- [x] Add current-analysis report link.
- [x] Add current-analysis failed/no-report state.
- [x] Add Runs detail report action and failed/no-report state.
- [x] Add mocked browser smoke for completed and failed analysis observability.
- [x] Verify frontend build.
- [x] Verify existing paper workflow smoke still passes.
- [x] Update roadmap and project docs.
- [x] Update Yasin Brain log.

## Verification

- Ubuntu temp copy: `npm run build`
  - Result: passed.
- Ubuntu temp copy: `npx playwright test --config playwright.config.ts e2e/analysis-observability-smoke.spec.ts`
  - Result: 1 passed.
- Ubuntu temp copy: `npx playwright test --config playwright.config.ts e2e/paper-workflow-smoke.spec.ts`
  - Result: 1 passed.

