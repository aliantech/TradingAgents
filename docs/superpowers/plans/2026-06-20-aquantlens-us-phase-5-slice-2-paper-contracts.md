# AQuantLens US Phase 5 Slice 2 Paper Trading Domain Contracts Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add backend paper-trading domain contract schemas and tests without persistence, API routes, broker adapters, or live execution behavior.

**Architecture:** Create a new isolated `app.paper_trading` package that owns paper-only Pydantic contracts. Keep this slice at the typed contract layer: no SQLAlchemy models, no FastAPI router, no frontend changes, and no broker SDK imports. Tests verify allowed statuses, numeric constraints, source references, paper-only audit events, and forbidden broker/live fields.

**Tech Stack:** Python 3.12, Pydantic v2, pytest, FastAPI backend package layout.

---

## Scope

This plan implements Phase 5 Slice 2 only.

Included:

- `PaperAccount`
- `PaperOrderIntent`
- `RiskDecision`
- `PaperFill`
- `PaperPosition`
- `PaperAuditEvent`
- contract tests
- paper-only grep checks
- roadmap status update

Excluded:

- database persistence
- SQL migrations
- API endpoints
- frontend UI
- RiskGuard service logic
- paper execution adapter
- broker integration
- live execution
- MCP trading tools

## File Structure

- Create `backend/app/paper_trading/__init__.py`
  - Exposes the paper trading package.
- Create `backend/app/paper_trading/contracts.py`
  - Defines enums and Pydantic contracts for Phase 5 Slice 2.
- Create `backend/tests/test_paper_trading_contracts.py`
  - Covers valid contracts, invalid statuses, invalid numeric values, source references, paper-only audit events, and forbidden extra fields.
- Modify `docs/roadmap/phase-5-roadmap.md`
  - Mark Slice 2 as implemented after tests pass.
- Modify `PROJECT.md`
  - Update the current progress snapshot after Slice 2 is verified.

## Task 1: Add Failing Paper Contract Tests

**Files:**
- Create: `backend/tests/test_paper_trading_contracts.py`

- [ ] **Step 1: Write the failing test file**

Create `backend/tests/test_paper_trading_contracts.py` with this content:

```python
from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError

from app.paper_trading.contracts import (
    AssetClass,
    AuditOutcome,
    AuditResourceType,
    OrderIntentStatus,
    OrderSide,
    OrderSource,
    OrderType,
    PaperAccount,
    PaperAccountStatus,
    PaperAuditEvent,
    PaperFill,
    PaperOrderIntent,
    PaperPosition,
    RiskDecision,
    RiskDecisionResult,
    TimeInForce,
)


def test_paper_account_contract_is_simulated_and_active():
    account = PaperAccount(
        account_id=uuid4(),
        name="Default paper account",
        base_currency="USD",
        starting_cash=100_000,
        current_cash=100_000,
        status=PaperAccountStatus.ACTIVE,
        created_at=timestamp(),
    )

    assert account.base_currency == "USD"
    assert account.starting_cash == 100_000
    assert account.current_cash == 100_000
    assert account.status == PaperAccountStatus.ACTIVE
    assert "broker" not in account.model_dump()


def test_paper_account_rejects_non_positive_cash():
    with pytest.raises(ValidationError):
        PaperAccount(
            account_id=uuid4(),
            name="Bad paper account",
            base_currency="USD",
            starting_cash=0,
            current_cash=100_000,
            status=PaperAccountStatus.ACTIVE,
            created_at=timestamp(),
        )


def test_order_intent_contract_requires_paper_only_fields():
    candidate_id = uuid4()
    intent = PaperOrderIntent(
        intent_id=uuid4(),
        account_id=uuid4(),
        source=OrderSource.HUMAN,
        source_reference_id=candidate_id,
        symbol="SPY",
        asset_class=AssetClass.ETF,
        side=OrderSide.BUY,
        quantity=2,
        order_type=OrderType.LIMIT,
        limit_price=500.25,
        time_in_force=TimeInForce.DAY,
        status=OrderIntentStatus.DRAFT,
        idempotency_key="paper-intent-SPY-20260620-1",
        created_at=timestamp(),
    )

    assert intent.source_reference_id == candidate_id
    assert intent.status == OrderIntentStatus.DRAFT
    assert intent.limit_price == 500.25
    assert intent.asset_class == AssetClass.ETF
    assert "broker" not in intent.model_dump()


def test_order_intent_rejects_limit_order_without_limit_price():
    with pytest.raises(ValidationError):
        PaperOrderIntent(
            intent_id=uuid4(),
            account_id=uuid4(),
            source=OrderSource.HUMAN,
            source_reference_id=uuid4(),
            symbol="SPY",
            asset_class=AssetClass.ETF,
            side=OrderSide.BUY,
            quantity=1,
            order_type=OrderType.LIMIT,
            limit_price=None,
            time_in_force=TimeInForce.DAY,
            status=OrderIntentStatus.DRAFT,
            idempotency_key="missing-limit-price",
            created_at=timestamp(),
        )


def test_order_intent_rejects_broker_route_extra_field():
    with pytest.raises(ValidationError):
        PaperOrderIntent(
            intent_id=uuid4(),
            account_id=uuid4(),
            source=OrderSource.HUMAN,
            source_reference_id=uuid4(),
            symbol="SPY",
            asset_class=AssetClass.ETF,
            side=OrderSide.BUY,
            quantity=1,
            order_type=OrderType.MARKET,
            time_in_force=TimeInForce.DAY,
            status=OrderIntentStatus.DRAFT,
            idempotency_key="forbidden-broker-route",
            created_at=timestamp(),
            broker_route="LIVE",
        )


def test_risk_decision_contract_is_explicit_and_reasoned():
    intent_id = uuid4()
    decision = RiskDecision(
        decision_id=uuid4(),
        intent_id=intent_id,
        result=RiskDecisionResult.REJECT,
        reason_codes=["notional_limit_exceeded"],
        explanation="Estimated notional exceeds paper account limit.",
        estimated_notional=125_000,
        created_at=timestamp(),
    )

    assert decision.intent_id == intent_id
    assert decision.result == RiskDecisionResult.REJECT
    assert decision.reason_codes == ["notional_limit_exceeded"]
    assert decision.estimated_notional == 125_000


def test_paper_fill_and_position_contracts_are_simulated():
    account_id = uuid4()
    intent_id = uuid4()
    fill = PaperFill(
        fill_id=uuid4(),
        intent_id=intent_id,
        account_id=account_id,
        symbol="SPY",
        asset_class=AssetClass.ETF,
        side=OrderSide.BUY,
        quantity=2,
        fill_price=500.25,
        filled_at=timestamp(),
    )
    position = PaperPosition(
        position_id=uuid4(),
        account_id=account_id,
        symbol="SPY",
        asset_class=AssetClass.ETF,
        quantity=2,
        average_price=500.25,
        updated_at=timestamp(),
    )

    assert fill.intent_id == intent_id
    assert fill.quantity == 2
    assert fill.fill_price == 500.25
    assert position.quantity == 2
    assert position.average_price == 500.25


def test_audit_event_contract_records_paper_outcome_without_secrets():
    resource_id = uuid4()
    event = PaperAuditEvent(
        event_id=uuid4(),
        actor_type="human",
        resource_type=AuditResourceType.ORDER_INTENT,
        resource_id=resource_id,
        action="intent_created",
        outcome=AuditOutcome.SUCCESS,
        reason_code="created",
        message="Paper intent draft created.",
        created_at=timestamp(),
    )

    assert event.resource_id == resource_id
    assert event.outcome == AuditOutcome.SUCCESS
    assert event.reason_code == "created"
    assert "secret" not in str(event.model_dump()).lower()
    assert "credential" not in str(event.model_dump()).lower()


def test_uuid_fields_are_uuid_instances():
    account = PaperAccount(
        account_id=str(uuid4()),
        name="String uuid paper account",
        base_currency="USD",
        starting_cash=50_000,
        current_cash=50_000,
        status=PaperAccountStatus.ACTIVE,
        created_at=timestamp(),
    )

    assert isinstance(account.account_id, UUID)


def timestamp():
    return datetime(2026, 6, 20, 13, 30, tzinfo=UTC)
```

- [ ] **Step 2: Run the focused test and verify it fails for the missing module**

Run on Ubuntu:

```bash
ssh yasin-ubuntu 'cd /home/yasin/workspace/TradingAgents/backend && PYTHONPATH=. .venv/bin/python -m pytest -q tests/test_paper_trading_contracts.py --tb=short'
```

Expected: FAIL with `ModuleNotFoundError: No module named 'app.paper_trading'`.

## Task 2: Add Paper Trading Package and Contracts

**Files:**
- Create: `backend/app/paper_trading/__init__.py`
- Create: `backend/app/paper_trading/contracts.py`
- Test: `backend/tests/test_paper_trading_contracts.py`

- [ ] **Step 1: Create the package file**

Create `backend/app/paper_trading/__init__.py` with this content:

```python
"""Paper-only trading domain contracts."""
```

- [ ] **Step 2: Implement the minimal contract layer**

Create `backend/app/paper_trading/contracts.py` with this content:

```python
from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StrictContract(BaseModel):
    model_config = ConfigDict(extra="forbid")


class PaperAccountStatus(StrEnum):
    ACTIVE = "active"
    PAUSED = "paused"
    ARCHIVED = "archived"


class OrderSource(StrEnum):
    HUMAN = "human"
    AGENT = "agent"
    SYSTEM = "system"


class AssetClass(StrEnum):
    EQUITY = "equity"
    ETF = "etf"
    INDEX_OPTION = "index-option"
    EQUITY_OPTION = "equity-option"


class OrderSide(StrEnum):
    BUY = "buy"
    SELL = "sell"


class OrderType(StrEnum):
    MARKET = "market"
    LIMIT = "limit"


class TimeInForce(StrEnum):
    DAY = "day"
    GTC = "gtc"


class OrderIntentStatus(StrEnum):
    DRAFT = "draft"
    RISK_REJECTED = "risk_rejected"
    AWAITING_REVIEW = "awaiting_review"
    APPROVED_FOR_PAPER = "approved_for_paper"
    PAPER_SUBMITTED = "paper_submitted"
    PAPER_FILLED = "paper_filled"
    PAPER_CANCELLED = "paper_cancelled"


class RiskDecisionResult(StrEnum):
    PASS = "pass"
    REJECT = "reject"


class AuditResourceType(StrEnum):
    ORDER_INTENT = "order_intent"
    RISK_DECISION = "risk_decision"
    PAPER_FILL = "paper_fill"
    PAPER_POSITION = "paper_position"


class AuditOutcome(StrEnum):
    SUCCESS = "success"
    DENIED = "denied"
    ERROR = "error"


class PaperAccount(StrictContract):
    account_id: UUID
    name: str = Field(min_length=1, max_length=120)
    base_currency: str = Field(default="USD", min_length=3, max_length=3)
    starting_cash: float = Field(gt=0)
    current_cash: float
    status: PaperAccountStatus
    created_at: datetime


class PaperOrderIntent(StrictContract):
    intent_id: UUID
    account_id: UUID
    source: OrderSource
    source_reference_id: UUID
    symbol: str = Field(min_length=1, max_length=64)
    asset_class: AssetClass
    side: OrderSide
    quantity: float = Field(gt=0)
    order_type: OrderType
    limit_price: float | None = Field(default=None, gt=0)
    time_in_force: TimeInForce
    status: OrderIntentStatus
    idempotency_key: str = Field(min_length=8, max_length=160)
    created_at: datetime

    @model_validator(mode="after")
    def require_limit_price_for_limit_orders(self) -> "PaperOrderIntent":
        if self.order_type == OrderType.LIMIT and self.limit_price is None:
            raise ValueError("limit_price is required for limit orders")
        return self


class RiskDecision(StrictContract):
    decision_id: UUID
    intent_id: UUID
    result: RiskDecisionResult
    reason_codes: list[str] = Field(min_length=1)
    explanation: str = Field(min_length=1, max_length=500)
    estimated_notional: float = Field(ge=0)
    created_at: datetime


class PaperFill(StrictContract):
    fill_id: UUID
    intent_id: UUID
    account_id: UUID
    symbol: str = Field(min_length=1, max_length=64)
    asset_class: AssetClass
    side: OrderSide
    quantity: float = Field(gt=0)
    fill_price: float = Field(gt=0)
    filled_at: datetime


class PaperPosition(StrictContract):
    position_id: UUID
    account_id: UUID
    symbol: str = Field(min_length=1, max_length=64)
    asset_class: AssetClass
    quantity: float
    average_price: float = Field(ge=0)
    updated_at: datetime


class PaperAuditEvent(StrictContract):
    event_id: UUID
    actor_type: str = Field(min_length=1, max_length=64)
    resource_type: AuditResourceType
    resource_id: UUID
    action: str = Field(min_length=1, max_length=120)
    outcome: AuditOutcome
    reason_code: str = Field(min_length=1, max_length=120)
    message: str = Field(min_length=1, max_length=500)
    created_at: datetime
```

- [ ] **Step 3: Run the focused contract test**

Run on Ubuntu:

```bash
ssh yasin-ubuntu 'cd /home/yasin/workspace/TradingAgents/backend && PYTHONPATH=. .venv/bin/python -m pytest -q tests/test_paper_trading_contracts.py --tb=short'
```

Expected: PASS, `9 passed`.

## Task 3: Add Contract Export Coverage

**Files:**
- Modify: `backend/app/paper_trading/__init__.py`
- Modify: `backend/tests/test_paper_trading_contracts.py`

- [ ] **Step 1: Add a failing package export test**

Append this test to `backend/tests/test_paper_trading_contracts.py`:

```python
def test_paper_trading_package_exports_contracts():
    import app.paper_trading as paper_trading

    assert paper_trading.PaperAccount is PaperAccount
    assert paper_trading.PaperOrderIntent is PaperOrderIntent
    assert paper_trading.RiskDecision is RiskDecision
    assert paper_trading.PaperFill is PaperFill
    assert paper_trading.PaperPosition is PaperPosition
    assert paper_trading.PaperAuditEvent is PaperAuditEvent
```

- [ ] **Step 2: Run the focused test and verify it fails for missing exports**

Run on Ubuntu:

```bash
ssh yasin-ubuntu 'cd /home/yasin/workspace/TradingAgents/backend && PYTHONPATH=. .venv/bin/python -m pytest -q tests/test_paper_trading_contracts.py::test_paper_trading_package_exports_contracts --tb=short'
```

Expected: FAIL with `AttributeError: module 'app.paper_trading' has no attribute 'PaperAccount'`.

- [ ] **Step 3: Export the contract names**

Replace `backend/app/paper_trading/__init__.py` with this content:

```python
"""Paper-only trading domain contracts."""

from app.paper_trading.contracts import (
    AssetClass,
    AuditOutcome,
    AuditResourceType,
    OrderIntentStatus,
    OrderSide,
    OrderSource,
    OrderType,
    PaperAccount,
    PaperAccountStatus,
    PaperAuditEvent,
    PaperFill,
    PaperOrderIntent,
    PaperPosition,
    RiskDecision,
    RiskDecisionResult,
    TimeInForce,
)

__all__ = [
    "AssetClass",
    "AuditOutcome",
    "AuditResourceType",
    "OrderIntentStatus",
    "OrderSide",
    "OrderSource",
    "OrderType",
    "PaperAccount",
    "PaperAccountStatus",
    "PaperAuditEvent",
    "PaperFill",
    "PaperOrderIntent",
    "PaperPosition",
    "RiskDecision",
    "RiskDecisionResult",
    "TimeInForce",
]
```

- [ ] **Step 4: Run focused contract tests**

Run on Ubuntu:

```bash
ssh yasin-ubuntu 'cd /home/yasin/workspace/TradingAgents/backend && PYTHONPATH=. .venv/bin/python -m pytest -q tests/test_paper_trading_contracts.py --tb=short'
```

Expected: PASS, `10 passed`.

## Task 4: Run Safety Grep and Backend Regression

**Files:**
- No file changes.

- [ ] **Step 1: Confirm no broker or live execution implementation was introduced**

Run locally or on Ubuntu:

```bash
rg -n "broker|live execution|place_order|submit_order|ibkr|alpaca|order_id|account_number" backend/app/paper_trading backend/tests/test_paper_trading_contracts.py
```

Expected: either no output or only paper-only test names/comments that explicitly reject broker/live fields. If implementation code contains broker routes, broker SDK names, live order ids, or account numbers, stop and remove them.

- [ ] **Step 2: Run focused tests on Ubuntu**

```bash
ssh yasin-ubuntu 'cd /home/yasin/workspace/TradingAgents/backend && PYTHONPATH=. .venv/bin/python -m pytest -q tests/test_paper_trading_contracts.py --tb=short'
```

Expected: PASS, `10 passed`.

- [ ] **Step 3: Run full backend regression on Ubuntu**

```bash
ssh yasin-ubuntu 'cd /home/yasin/workspace/TradingAgents/backend && PYTHONPATH=. .venv/bin/python -m pytest -q --tb=short'
```

Expected: PASS with the previous 140 tests plus the new 10 paper contract tests.

## Task 5: Update Documentation After Verification

**Files:**
- Modify: `docs/roadmap/phase-5-roadmap.md`
- Modify: `PROJECT.md`

- [ ] **Step 1: Update Slice 2 status in the roadmap**

In `docs/roadmap/phase-5-roadmap.md`, replace:

```markdown
### Slice 2: Paper Trading Domain Contracts

Status: pending Slice 1 approval.
```

with:

```markdown
### Slice 2: Paper Trading Domain Contracts

Status: implemented and validated on 2026-06-20.
```

Then add this under `Planned deliverables:` after implementation:

```markdown
Implemented:

- Added `backend/app/paper_trading/contracts.py` for paper-only domain contracts.
- Added `PaperAccount`, `PaperOrderIntent`, `RiskDecision`, `PaperFill`, `PaperPosition`, and `PaperAuditEvent`.
- Added enum boundaries for account status, source, asset class, side, order type, time in force, intent status, risk decision result, audit resource type, and audit outcome.
- Added contract tests for valid objects, rejected invalid cash, rejected missing limit price, rejected broker-route extra fields, simulated fills/positions, audit events, and package exports.
```

- [ ] **Step 2: Update project status snapshot**

In `PROJECT.md`, update the current Phase 5 state paragraph so it says Slice 2 paper trading domain contracts are implemented and validated, while persistence, API, adapter, UI, and broker execution remain out of scope.

Use this wording:

```markdown
- Current Phase 5 state: Phase 5 is in paper-only planning and early contract implementation. Phase 4 completed the approved research-only Strategy Lab experiment workbench scope. Phase 5 now has paper-only architecture documentation plus backend domain contracts for paper accounts, order intents, risk decisions, paper fills, paper positions, and paper audit events. Persistence, APIs, RiskGuard service logic, paper adapter execution, UI promotion flows, live broker execution, broker credentials, broker account mutation, AI-directed live trading, trading-scope MCP tools, and automatic paper-to-live promotion remain out of scope.
```

- [ ] **Step 3: Run docs diff check**

```bash
git diff -- docs/roadmap/phase-5-roadmap.md PROJECT.md
```

Expected: only Slice 2 status/evidence and project snapshot changes.

## Task 6: Final Verification, Commit, and Push

**Files:**
- Stage all files touched in this implementation.

- [ ] **Step 1: Run whitespace check**

```bash
git diff --check
```

Expected: no output.

- [ ] **Step 2: Run final focused tests on Ubuntu**

```bash
ssh yasin-ubuntu 'cd /home/yasin/workspace/TradingAgents/backend && PYTHONPATH=. .venv/bin/python -m pytest -q tests/test_paper_trading_contracts.py --tb=short'
```

Expected: PASS, `10 passed`.

- [ ] **Step 3: Run final full backend regression on Ubuntu**

```bash
ssh yasin-ubuntu 'cd /home/yasin/workspace/TradingAgents/backend && PYTHONPATH=. .venv/bin/python -m pytest -q --tb=short'
```

Expected: PASS with the new paper contract tests included.

- [ ] **Step 4: Stage implementation files**

```bash
git add backend/app/paper_trading/__init__.py backend/app/paper_trading/contracts.py backend/tests/test_paper_trading_contracts.py docs/roadmap/phase-5-roadmap.md PROJECT.md
```

- [ ] **Step 5: Commit**

```bash
git commit -m "feat: add paper trading domain contracts"
```

- [ ] **Step 6: Push**

```bash
git push origin aquantlens-us
```

## Self-Review Checklist

- Spec coverage: Slice 2 implements paper contract schemas only; RiskGuard, persistence, API, adapter, and UI are deferred to later slices.
- Placeholder scan: this plan contains no placeholders for implementation behavior.
- Type consistency: enum and model names are consistent across tests, exports, and contract implementation.
- Safety boundary: implementation must not add broker credentials, live order ids, broker routes, broker SDK calls, or execution adapters.
