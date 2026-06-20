# Phase 6 Slice 4 Paper PnL Snapshot Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use test-driven development for calculation behavior and API behavior. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add paper-only PnL snapshot logic using explicit caller-provided reference prices.

**Architecture:** Add a pure `paper_trading.pnl` module and expose it through a read-only FastAPI endpoint. The endpoint uses existing paper account, position, and fill rows plus request-provided reference prices; it does not fetch quotes, store prices, call broker APIs, or expose live execution fields.

**Tech Stack:** FastAPI, Pydantic contracts, SQLAlchemy repository, pytest.

---

## File Structure

- Create: `backend/app/paper_trading/pnl.py`
  - Add reference price, position PnL, and snapshot contracts.
  - Add pure unrealized PnL, account equity, stale/missing price state, option multiplier, and realized PnL helpers.
- Modify: `backend/app/paper_trading/repository.py`
  - Add account-scoped fill listing for local realized PnL calculation.
- Modify: `backend/app/paper_trading/router.py`
  - Add `POST /api/paper-trading/accounts/{account_id}/pnl-snapshot`.
- Create: `backend/tests/test_paper_trading_pnl.py`
  - Add pure calculation coverage.
- Modify: `backend/tests/test_paper_trading_api.py`
  - Add API coverage for caller-provided prices and missing-price state.
- Modify: `docs/roadmap/phase-6-roadmap.md`
  - Record Slice 4 implementation and verification.
- Modify: `PROJECT.md`
  - Update current Phase 6 state and key documents.

## Assumptions

- Reference prices are supplied by the caller in the API request.
- Stale and missing reference prices should not be used for market value or unrealized PnL totals.
- Account equity is current paper cash plus market value for positions with fresh reference prices.
- Realized PnL can be derived from local paper fills for current long-only sell flows; production-grade tax-lot accounting remains out of scope.

## Safety Boundary

This slice must not add:

- Broker SDKs.
- Broker credentials.
- Broker account fields.
- Live order fields.
- External quote fetches inside PnL calculation.
- Trading-scope MCP tools.
- Live-trading UI controls.
- Paper-to-live promotion.

## Tasks

- [x] Add pure PnL tests for equity/ETF, options, stale/missing prices, and short-like position quantities.
- [x] Add API tests for caller-provided reference prices and missing-price state.
- [x] Add pure PnL snapshot module.
- [x] Add account-scoped fill listing for realized PnL.
- [x] Add paper PnL snapshot API endpoint.
- [x] Verify focused backend tests on Ubuntu.
- [x] Update project documentation.

## Verification

- Local: `python3 -m py_compile backend/app/paper_trading/pnl.py backend/app/paper_trading/repository.py backend/app/paper_trading/router.py backend/tests/test_paper_trading_pnl.py backend/tests/test_paper_trading_api.py`
- Ubuntu temp copy: `/home/yasin/workspace/TradingAgents/backend/.venv/bin/python -m pytest backend/tests/test_paper_trading_pnl.py backend/tests/test_paper_trading_api.py backend/tests/test_paper_trading_repository.py -q`

