# Phase 6 Slice 5 Paper Risk Dashboard UI Implementation Plan

> **For agentic workers:** Keep this slice UI-only except for API client wiring. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a compact Strategy Lab paper risk dashboard so operators can inspect paper cash, positions, PnL, recent paper intents, fills, and audit state.

**Architecture:** Reuse the Slice 3 summary API and Slice 4 PnL snapshot API from the existing Strategy Lab page. The UI submits explicit reference prices derived from already-loaded market bars; it does not fetch new quotes, connect to brokers, add live controls, or create paper-to-live promotion.

**Tech Stack:** React, Vite, TypeScript, existing shadcn-style UI components, Playwright smoke test.

---

## File Structure

- Modify: `frontend/src/lib/api.ts`
  - Add paper account summary and paper PnL snapshot response types.
  - Add API client methods for summary and PnL snapshot.
- Modify: `frontend/src/features/strategy-lab/StrategyLabPanel.tsx`
  - Add paper dashboard state, loading/error handling, refresh action, and compact dashboard UI.
  - Refresh dashboard after paper submit.
- Modify: `frontend/e2e/paper-workflow-smoke.spec.ts`
  - Mock summary and PnL APIs.
  - Assert paper dashboard and equity state are visible after paper submit.
- Modify: `docs/roadmap/phase-6-roadmap.md`
  - Record Slice 5 implementation and verification.
- Modify: `PROJECT.md`
  - Update current Phase 6 state and key documents.

## Assumptions

- The Strategy Lab page already has enough loaded bars to provide a current paper reference price for matching equity/ETF positions.
- Positions without a matching loaded bar should rely on the backend PnL snapshot's missing-price state.
- This first dashboard should be compact and operator-focused, not a new top-level route.

## Safety Boundary

This slice must not add:

- Broker SDKs.
- Broker credentials.
- Broker account fields.
- Live order fields.
- External quote fetches for PnL.
- Trading-scope MCP tools.
- Live-trading UI controls.
- Paper-to-live promotion.

## Tasks

- [x] Add frontend API types and methods for paper summary and PnL snapshot.
- [x] Add Strategy Lab paper risk dashboard state and refresh flow.
- [x] Render cash, equity, PnL, positions, price state, recent intents/fills, and audit preview.
- [x] Refresh dashboard after local paper submit.
- [x] Extend Playwright paper smoke mocks and assertions.
- [x] Verify TypeScript, backend focused tests, frontend build, and Playwright smoke on Ubuntu.
- [x] Update project documentation.

## Verification

- Local: `npm exec tsc -- -p tsconfig.json --noEmit`
- Ubuntu temp copy: `/home/yasin/workspace/TradingAgents/backend/.venv/bin/python -m pytest backend/tests/test_paper_trading_pnl.py backend/tests/test_paper_trading_api.py backend/tests/test_paper_trading_repository.py -q`
- Ubuntu temp copy: `cd frontend && npm run build`
- Ubuntu temp copy: `cd frontend && npx playwright test e2e/paper-workflow-smoke.spec.ts`

