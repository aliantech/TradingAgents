# Phase 6 Slice 3 Paper Account Summary API Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a compact paper-only account summary endpoint for UI and operator inspection.

**Architecture:** Extend the existing paper trading repository and FastAPI router. The endpoint reads existing paper account, position, intent, fill, and audit rows; it does not calculate PnL, fetch market data, or introduce broker/live execution fields.

**Tech Stack:** FastAPI, SQLAlchemy repository, pytest.

---

## File Structure

- Modify: `backend/app/paper_trading/repository.py`
  - Add account-scoped recent fill and recent audit queries.
- Modify: `backend/app/paper_trading/router.py`
  - Add `GET /api/paper-trading/accounts/{account_id}/summary`.
  - Add response models for paper positions, paper fills, and paper account summary.
- Modify: `backend/tests/test_paper_trading_api.py`
  - Add summary endpoint account-scope and safety-field tests.
- Modify: `docs/roadmap/phase-6-roadmap.md`
  - Record Slice 3 implementation and verification.
- Modify: `PROJECT.md`
  - Update current Phase 6 state and key documents.

## Assumptions

- Account summary should be read-only.
- Existing paper position and fill rows are sufficient for the first operator snapshot.
- Recent intents can reuse the existing account-scoped `list_order_intents` limit.
- Recent audit events should include resources belonging to the account only.
- PnL, market value, reference prices, and stale-price state belong to Slice 4.

## Safety Boundary

This slice must not add:

- Broker SDKs.
- Broker credentials.
- Broker account fields.
- Live order fields.
- Trading-scope MCP tools.
- Live-trading UI controls.
- Paper-to-live promotion.

## Tasks

- [x] Add failing API tests for account-scoped summary output and missing-account behavior.
- [x] Add repository methods for account-scoped recent fills and audit events.
- [x] Add summary route and response mappers.
- [x] Verify backend paper API and repository tests on Ubuntu.
- [x] Update project documentation.

## Verification

- Local: `python3 -m py_compile backend/app/paper_trading/repository.py backend/app/paper_trading/router.py backend/tests/test_paper_trading_api.py`
- Ubuntu temp copy: `/home/yasin/workspace/TradingAgents/backend/.venv/bin/python -m pytest backend/tests/test_paper_trading_api.py backend/tests/test_paper_trading_repository.py -q`

