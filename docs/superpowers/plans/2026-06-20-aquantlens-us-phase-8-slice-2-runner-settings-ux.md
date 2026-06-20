# Phase 8 Slice 2 Runner Mode Settings UX Plan

> **For agentic workers:** This slice updates settings visibility only. Do not call providers or change runner execution behavior.

**Goal:** Make deterministic versus real TradingAgents runner mode visible and editable in Settings through the existing persisted settings APIs.

## File Structure

- Modify: `frontend/src/features/settings/settingsCatalog.ts`
  - Add model/agent settings entries for `AQUANTLENS_TRADINGAGENTS_*` runtime keys.
  - Keep secret API keys out of the model/agent settings section.
- Modify: `frontend/src/app/App.tsx`
  - Add select controls for runner mode, runner provider, and output language.
  - Add display labels and defaults for persisted runner settings.
- Modify: `frontend/src/i18n/index.ts`
  - Add Chinese and English copy explaining deterministic default and real-runner prerequisites.
- Modify: `frontend/src/features/settings/settingsCatalog.test.ts`
  - Verify required runner runtime keys appear in model settings.
  - Verify model settings do not display API-key secrets.
- Create: `frontend/e2e/settings-runner-mode-smoke.spec.ts`
  - Mock settings API.
  - Verify runner mode visibility and `real-tradingagents` option without provider calls.
- Modify: `docs/roadmap/phase-8-roadmap.md`
  - Mark Slice 2 complete and record verification.
- Modify: `PROJECT.md`
  - Update current Phase 8 status.
- Modify: `/Users/yasin/Documents/Yasin AI OS/04-Projects/aquantlens/LOG.md`
  - Record Slice 2 implementation for the separate US/options branch.

## Safety Boundary

This slice must not add:

- Provider calls.
- Secret-value display.
- Broker SDKs.
- Broker credentials.
- Broker account mutation.
- Live order methods.
- AI-directed live trading.
- Trading-scope MCP tools.
- Live-trading UI controls.
- Paper-to-live promotion.

## Tasks

- [x] Add runner runtime settings to model/agent settings catalog.
- [x] Add runner mode/provider/output select controls.
- [x] Add display labels and defaults.
- [x] Add Chinese/English copy for deterministic default and real-runner prerequisites.
- [x] Add catalog test coverage.
- [x] Add mocked browser smoke.
- [x] Update roadmap and project docs.
- [x] Update Yasin Brain log.

## Verification

- Local: `node frontend/src/features/settings/settingsCatalog.test.ts`
- Ubuntu temp copy: `node src/features/settings/settingsCatalog.test.ts`
- Ubuntu temp copy: `npm run build`
- Ubuntu temp copy: `npx playwright test --config playwright.config.ts e2e/settings-runner-mode-smoke.spec.ts`
  - Result: 1 passed.

