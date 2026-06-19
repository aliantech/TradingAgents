# AQuantLens US Phase 5 Slice 4 Paper Persistence and Audit Log Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add database-backed paper account, order intent, risk decision, paper fill, paper position, and append-only audit persistence without adding API routes, frontend UI, paper execution adapters, broker adapters, or live execution behavior.

**Architecture:** Extend the existing SQLAlchemy model layer and `schema.sql`, then add a small `PaperTradingRepository` under `app.paper_trading`. The repository converts between Slice 2/3 Pydantic contracts and SQLAlchemy models, commits explicit state changes, and appends audit records through a helper that never updates or deletes prior audit rows.

**Tech Stack:** Python 3.12, SQLAlchemy ORM, SQLite test database via `Base.metadata.create_all`, existing `app.db.models`, pytest.

---

## Scope

This plan implements Phase 5 Slice 4 only.

Included:

- SQLAlchemy models for paper accounts, intents, risk decisions, fills, positions, and audit events.
- `schema.sql` table definitions and indexes.
- `PaperTradingRepository`.
- Append-only audit helper.
- Tests against temporary SQLite.
- Safety grep checks.
- Roadmap and project status updates.

Excluded:

- API endpoints.
- Frontend UI.
- RiskGuard behavior changes.
- Paper execution adapter.
- Broker integration.
- Live execution.
- MCP trading tools.
- Broker credentials or account identifiers.

## File Structure

- Modify `backend/app/db/models.py`
  - Add six paper persistence models.
- Modify `backend/app/db/schema.sql`
  - Add six paper persistence tables and indexes.
- Create `backend/app/paper_trading/repository.py`
  - Add repository methods for saving accounts, intents, decisions, fills, positions, and append-only audit records.
- Create `backend/tests/test_paper_trading_repository.py`
  - Add SQLite persistence tests and append-only audit tests.
- Modify `docs/roadmap/phase-5-roadmap.md`
  - Mark Slice 4 implemented after verification.
- Modify `PROJECT.md`
  - Update current Phase 5 state after verification.

## Table Names

Use these exact names:

- `paper_accounts`
- `paper_order_intents`
- `paper_risk_decisions`
- `paper_fills`
- `paper_positions`
- `paper_audit_events`

## Task 1: Add Failing Repository Persistence Tests

**Files:**
- Create: `backend/tests/test_paper_trading_repository.py`

- [ ] **Step 1: Write the failing test file**

Create `backend/tests/test_paper_trading_repository.py` with this content:

```python
from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.db.models import PaperAuditEventModel
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
from app.paper_trading.repository import PaperTradingRepository


def test_repository_persists_account_intent_decision_fill_and_position():
    session = _session()
    repository = PaperTradingRepository(session)
    account = paper_account()
    intent = paper_intent(account.account_id)
    decision = risk_decision(intent.intent_id)
    fill = paper_fill(account.account_id, intent.intent_id)
    position = paper_position(account.account_id)

    repository.save_account(account)
    repository.save_order_intent(intent)
    repository.save_risk_decision(decision)
    repository.save_fill(fill)
    repository.save_position(position)

    assert repository.get_account(account.account_id) == account
    assert repository.get_order_intent(intent.intent_id) == intent
    assert repository.get_risk_decision(decision.decision_id) == decision
    assert repository.list_fills_for_intent(intent.intent_id) == [fill]
    assert repository.get_position(position.position_id) == position


def test_repository_appends_audit_events_without_mutating_existing_rows():
    session = _session()
    repository = PaperTradingRepository(session)
    resource_id = uuid4()
    first = audit_event(resource_id, reason_code="created")
    second = audit_event(resource_id, reason_code="risk_passed")

    repository.append_audit_event(first)
    repository.append_audit_event(second)

    rows = session.scalars(
        select(PaperAuditEventModel).order_by(PaperAuditEventModel.created_at.asc())
    ).all()
    assert [row.reason_code for row in rows] == ["created", "risk_passed"]
    assert repository.list_audit_events(resource_id) == [first, second]


def test_repository_does_not_store_broker_or_live_execution_fields():
    session = _session()
    repository = PaperTradingRepository(session)
    account = paper_account()
    intent = paper_intent(account.account_id)

    repository.save_account(account)
    repository.save_order_intent(intent)

    stored_intent = repository.get_order_intent(intent.intent_id)
    dumped = stored_intent.model_dump()
    assert "broker" not in dumped
    assert "live" not in str(dumped).lower()


def _session():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def paper_account():
    return PaperAccount(
        account_id=uuid4(),
        name="Default paper account",
        base_currency="USD",
        starting_cash=100_000,
        current_cash=100_000,
        status=PaperAccountStatus.ACTIVE,
        created_at=timestamp(),
    )


def paper_intent(account_id):
    return PaperOrderIntent(
        intent_id=uuid4(),
        account_id=account_id,
        source=OrderSource.HUMAN,
        source_reference_id=uuid4(),
        symbol="SPY",
        asset_class=AssetClass.ETF,
        side=OrderSide.BUY,
        quantity=2,
        order_type=OrderType.MARKET,
        time_in_force=TimeInForce.DAY,
        status=OrderIntentStatus.DRAFT,
        idempotency_key=f"paper-intent-{uuid4()}",
        created_at=timestamp(),
    )


def risk_decision(intent_id):
    return RiskDecision(
        decision_id=uuid4(),
        intent_id=intent_id,
        result=RiskDecisionResult.PASS,
        reason_codes=["risk_checks_passed"],
        explanation="RiskGuard checks passed for paper simulation.",
        estimated_notional=1_000,
        created_at=timestamp(),
    )


def paper_fill(account_id, intent_id):
    return PaperFill(
        fill_id=uuid4(),
        intent_id=intent_id,
        account_id=account_id,
        symbol="SPY",
        asset_class=AssetClass.ETF,
        side=OrderSide.BUY,
        quantity=2,
        fill_price=500,
        filled_at=timestamp(),
    )


def paper_position(account_id):
    return PaperPosition(
        position_id=uuid4(),
        account_id=account_id,
        symbol="SPY",
        asset_class=AssetClass.ETF,
        quantity=2,
        average_price=500,
        updated_at=timestamp(),
    )


def audit_event(resource_id, *, reason_code):
    return PaperAuditEvent(
        event_id=uuid4(),
        actor_type="human",
        resource_type=AuditResourceType.ORDER_INTENT,
        resource_id=resource_id,
        action="paper_transition",
        outcome=AuditOutcome.SUCCESS,
        reason_code=reason_code,
        message=f"Audit event: {reason_code}.",
        created_at=timestamp(),
    )


def timestamp():
    return datetime(2026, 6, 20, 13, 30, tzinfo=UTC)
```

- [ ] **Step 2: Run the focused test and verify it fails for missing persistence**

Run on Ubuntu temporary clone:

```bash
ssh yasin-ubuntu 'cd /tmp/<slice4-clone>/backend && PYTHONPATH=. /home/yasin/workspace/TradingAgents/backend/.venv/bin/python -m pytest -q tests/test_paper_trading_repository.py --tb=short'
```

Expected: FAIL because `PaperAuditEventModel` or `PaperTradingRepository` does not exist.

## Task 2: Add SQLAlchemy Paper Models

**Files:**
- Modify: `backend/app/db/models.py`
- Test: `backend/tests/test_paper_trading_repository.py`

- [ ] **Step 1: Add paper persistence models**

Append these models to `backend/app/db/models.py` after `OptionSnapshotModel`:

```python
class PaperAccountModel(Base):
    __tablename__ = "paper_accounts"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    base_currency: Mapped[str] = mapped_column(String(3), default="USD")
    starting_cash: Mapped[float] = mapped_column(Float)
    current_cash: Mapped[float] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String(32), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class PaperOrderIntentModel(Base):
    __tablename__ = "paper_order_intents"
    __table_args__ = (
        UniqueConstraint("account_id", "idempotency_key", name="uq_paper_intents_account_idempotency"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True)
    account_id: Mapped[UUID] = mapped_column(ForeignKey("paper_accounts.id"), index=True)
    source: Mapped[str] = mapped_column(String(32), index=True)
    source_reference_id: Mapped[UUID] = mapped_column(index=True)
    symbol: Mapped[str] = mapped_column(String(64), index=True)
    asset_class: Mapped[str] = mapped_column(String(32), index=True)
    side: Mapped[str] = mapped_column(String(8))
    quantity: Mapped[float] = mapped_column(Float)
    order_type: Mapped[str] = mapped_column(String(16))
    limit_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    time_in_force: Mapped[str] = mapped_column(String(16))
    status: Mapped[str] = mapped_column(String(32), index=True)
    idempotency_key: Mapped[str] = mapped_column(String(160), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class PaperRiskDecisionModel(Base):
    __tablename__ = "paper_risk_decisions"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    intent_id: Mapped[UUID] = mapped_column(ForeignKey("paper_order_intents.id"), index=True)
    result: Mapped[str] = mapped_column(String(16), index=True)
    reason_codes: Mapped[list[str]] = mapped_column(JSON, default=list)
    explanation: Mapped[str] = mapped_column(Text)
    estimated_notional: Mapped[float] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class PaperFillModel(Base):
    __tablename__ = "paper_fills"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    intent_id: Mapped[UUID] = mapped_column(ForeignKey("paper_order_intents.id"), index=True)
    account_id: Mapped[UUID] = mapped_column(ForeignKey("paper_accounts.id"), index=True)
    symbol: Mapped[str] = mapped_column(String(64), index=True)
    asset_class: Mapped[str] = mapped_column(String(32), index=True)
    side: Mapped[str] = mapped_column(String(8))
    quantity: Mapped[float] = mapped_column(Float)
    fill_price: Mapped[float] = mapped_column(Float)
    filled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)


class PaperPositionModel(Base):
    __tablename__ = "paper_positions"
    __table_args__ = (
        UniqueConstraint("account_id", "symbol", "asset_class", name="uq_paper_positions_account_symbol_asset"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True)
    account_id: Mapped[UUID] = mapped_column(ForeignKey("paper_accounts.id"), index=True)
    symbol: Mapped[str] = mapped_column(String(64), index=True)
    asset_class: Mapped[str] = mapped_column(String(32), index=True)
    quantity: Mapped[float] = mapped_column(Float)
    average_price: Mapped[float] = mapped_column(Float)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class PaperAuditEventModel(Base):
    __tablename__ = "paper_audit_events"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    actor_type: Mapped[str] = mapped_column(String(64), index=True)
    resource_type: Mapped[str] = mapped_column(String(64), index=True)
    resource_id: Mapped[UUID] = mapped_column(index=True)
    action: Mapped[str] = mapped_column(String(120), index=True)
    outcome: Mapped[str] = mapped_column(String(32), index=True)
    reason_code: Mapped[str] = mapped_column(String(120), index=True)
    message: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, index=True)
```

- [ ] **Step 2: Run the focused test and verify the failure moves to missing repository**

Run:

```bash
ssh yasin-ubuntu 'cd /tmp/<slice4-clone>/backend && PYTHONPATH=. /home/yasin/workspace/TradingAgents/backend/.venv/bin/python -m pytest -q tests/test_paper_trading_repository.py --tb=short'
```

Expected: FAIL with `ModuleNotFoundError: No module named 'app.paper_trading.repository'`.

## Task 3: Add PaperTradingRepository

**Files:**
- Create: `backend/app/paper_trading/repository.py`
- Test: `backend/tests/test_paper_trading_repository.py`

- [ ] **Step 1: Create repository implementation**

Create `backend/app/paper_trading/repository.py` with this content:

```python
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import (
    PaperAccountModel,
    PaperAuditEventModel,
    PaperFillModel,
    PaperOrderIntentModel,
    PaperPositionModel,
    PaperRiskDecisionModel,
)
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


class PaperTradingRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def save_account(self, account: PaperAccount) -> PaperAccount:
        self.session.merge(
            PaperAccountModel(
                id=account.account_id,
                name=account.name,
                base_currency=account.base_currency,
                starting_cash=account.starting_cash,
                current_cash=account.current_cash,
                status=account.status.value,
                created_at=account.created_at,
            )
        )
        self.session.commit()
        return account

    def get_account(self, account_id: UUID) -> PaperAccount | None:
        model = self.session.get(PaperAccountModel, account_id)
        return to_account(model) if model else None

    def save_order_intent(self, intent: PaperOrderIntent) -> PaperOrderIntent:
        self.session.merge(
            PaperOrderIntentModel(
                id=intent.intent_id,
                account_id=intent.account_id,
                source=intent.source.value,
                source_reference_id=intent.source_reference_id,
                symbol=intent.symbol,
                asset_class=intent.asset_class.value,
                side=intent.side.value,
                quantity=intent.quantity,
                order_type=intent.order_type.value,
                limit_price=intent.limit_price,
                time_in_force=intent.time_in_force.value,
                status=intent.status.value,
                idempotency_key=intent.idempotency_key,
                created_at=intent.created_at,
            )
        )
        self.session.commit()
        return intent

    def get_order_intent(self, intent_id: UUID) -> PaperOrderIntent | None:
        model = self.session.get(PaperOrderIntentModel, intent_id)
        return to_order_intent(model) if model else None

    def save_risk_decision(self, decision: RiskDecision) -> RiskDecision:
        self.session.merge(
            PaperRiskDecisionModel(
                id=decision.decision_id,
                intent_id=decision.intent_id,
                result=decision.result.value,
                reason_codes=list(decision.reason_codes),
                explanation=decision.explanation,
                estimated_notional=decision.estimated_notional,
                created_at=decision.created_at,
            )
        )
        self.session.commit()
        return decision

    def get_risk_decision(self, decision_id: UUID) -> RiskDecision | None:
        model = self.session.get(PaperRiskDecisionModel, decision_id)
        return to_risk_decision(model) if model else None

    def save_fill(self, fill: PaperFill) -> PaperFill:
        self.session.merge(
            PaperFillModel(
                id=fill.fill_id,
                intent_id=fill.intent_id,
                account_id=fill.account_id,
                symbol=fill.symbol,
                asset_class=fill.asset_class.value,
                side=fill.side.value,
                quantity=fill.quantity,
                fill_price=fill.fill_price,
                filled_at=fill.filled_at,
            )
        )
        self.session.commit()
        return fill

    def list_fills_for_intent(self, intent_id: UUID) -> list[PaperFill]:
        models = self.session.scalars(
            select(PaperFillModel)
            .where(PaperFillModel.intent_id == intent_id)
            .order_by(PaperFillModel.filled_at.asc())
        ).all()
        return [to_fill(model) for model in models]

    def save_position(self, position: PaperPosition) -> PaperPosition:
        self.session.merge(
            PaperPositionModel(
                id=position.position_id,
                account_id=position.account_id,
                symbol=position.symbol,
                asset_class=position.asset_class.value,
                quantity=position.quantity,
                average_price=position.average_price,
                updated_at=position.updated_at,
            )
        )
        self.session.commit()
        return position

    def get_position(self, position_id: UUID) -> PaperPosition | None:
        model = self.session.get(PaperPositionModel, position_id)
        return to_position(model) if model else None

    def append_audit_event(self, event: PaperAuditEvent) -> PaperAuditEvent:
        self.session.add(
            PaperAuditEventModel(
                id=event.event_id,
                actor_type=event.actor_type,
                resource_type=event.resource_type.value,
                resource_id=event.resource_id,
                action=event.action,
                outcome=event.outcome.value,
                reason_code=event.reason_code,
                message=event.message,
                created_at=event.created_at,
            )
        )
        self.session.commit()
        return event

    def list_audit_events(self, resource_id: UUID) -> list[PaperAuditEvent]:
        models = self.session.scalars(
            select(PaperAuditEventModel)
            .where(PaperAuditEventModel.resource_id == resource_id)
            .order_by(PaperAuditEventModel.created_at.asc(), PaperAuditEventModel.id.asc())
        ).all()
        return [to_audit_event(model) for model in models]


def to_account(model: PaperAccountModel) -> PaperAccount:
    return PaperAccount(
        account_id=model.id,
        name=model.name,
        base_currency=model.base_currency,
        starting_cash=model.starting_cash,
        current_cash=model.current_cash,
        status=PaperAccountStatus(model.status),
        created_at=model.created_at,
    )


def to_order_intent(model: PaperOrderIntentModel) -> PaperOrderIntent:
    return PaperOrderIntent(
        intent_id=model.id,
        account_id=model.account_id,
        source=OrderSource(model.source),
        source_reference_id=model.source_reference_id,
        symbol=model.symbol,
        asset_class=AssetClass(model.asset_class),
        side=OrderSide(model.side),
        quantity=model.quantity,
        order_type=OrderType(model.order_type),
        limit_price=model.limit_price,
        time_in_force=TimeInForce(model.time_in_force),
        status=OrderIntentStatus(model.status),
        idempotency_key=model.idempotency_key,
        created_at=model.created_at,
    )


def to_risk_decision(model: PaperRiskDecisionModel) -> RiskDecision:
    return RiskDecision(
        decision_id=model.id,
        intent_id=model.intent_id,
        result=RiskDecisionResult(model.result),
        reason_codes=list(model.reason_codes),
        explanation=model.explanation,
        estimated_notional=model.estimated_notional,
        created_at=model.created_at,
    )


def to_fill(model: PaperFillModel) -> PaperFill:
    return PaperFill(
        fill_id=model.id,
        intent_id=model.intent_id,
        account_id=model.account_id,
        symbol=model.symbol,
        asset_class=AssetClass(model.asset_class),
        side=OrderSide(model.side),
        quantity=model.quantity,
        fill_price=model.fill_price,
        filled_at=model.filled_at,
    )


def to_position(model: PaperPositionModel) -> PaperPosition:
    return PaperPosition(
        position_id=model.id,
        account_id=model.account_id,
        symbol=model.symbol,
        asset_class=AssetClass(model.asset_class),
        quantity=model.quantity,
        average_price=model.average_price,
        updated_at=model.updated_at,
    )


def to_audit_event(model: PaperAuditEventModel) -> PaperAuditEvent:
    return PaperAuditEvent(
        event_id=model.id,
        actor_type=model.actor_type,
        resource_type=AuditResourceType(model.resource_type),
        resource_id=model.resource_id,
        action=model.action,
        outcome=AuditOutcome(model.outcome),
        reason_code=model.reason_code,
        message=model.message,
        created_at=model.created_at,
    )
```

- [ ] **Step 2: Run focused repository tests**

Run:

```bash
ssh yasin-ubuntu 'cd /tmp/<slice4-clone>/backend && PYTHONPATH=. /home/yasin/workspace/TradingAgents/backend/.venv/bin/python -m pytest -q tests/test_paper_trading_repository.py --tb=short'
```

Expected: PASS with all repository tests passing.

## Task 4: Add Schema SQL Tables and Indexes

**Files:**
- Modify: `backend/app/db/schema.sql`

- [ ] **Step 1: Add SQL DDL**

Append this block before the final index section in `backend/app/db/schema.sql`:

```sql
CREATE TABLE IF NOT EXISTS paper_accounts (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name text NOT NULL,
  base_currency text NOT NULL DEFAULT 'USD',
  starting_cash numeric(18, 6) NOT NULL,
  current_cash numeric(18, 6) NOT NULL,
  status text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS paper_order_intents (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  account_id uuid NOT NULL REFERENCES paper_accounts(id),
  source text NOT NULL,
  source_reference_id uuid NOT NULL,
  symbol text NOT NULL,
  asset_class text NOT NULL,
  side text NOT NULL,
  quantity numeric(18, 6) NOT NULL,
  order_type text NOT NULL,
  limit_price numeric(18, 6),
  time_in_force text NOT NULL,
  status text NOT NULL,
  idempotency_key text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT uq_paper_intents_account_idempotency UNIQUE (account_id, idempotency_key)
);

CREATE TABLE IF NOT EXISTS paper_risk_decisions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  intent_id uuid NOT NULL REFERENCES paper_order_intents(id),
  result text NOT NULL,
  reason_codes jsonb NOT NULL DEFAULT '[]'::jsonb,
  explanation text NOT NULL,
  estimated_notional numeric(18, 6) NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS paper_fills (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  intent_id uuid NOT NULL REFERENCES paper_order_intents(id),
  account_id uuid NOT NULL REFERENCES paper_accounts(id),
  symbol text NOT NULL,
  asset_class text NOT NULL,
  side text NOT NULL,
  quantity numeric(18, 6) NOT NULL,
  fill_price numeric(18, 6) NOT NULL,
  filled_at timestamptz NOT NULL
);

CREATE TABLE IF NOT EXISTS paper_positions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  account_id uuid NOT NULL REFERENCES paper_accounts(id),
  symbol text NOT NULL,
  asset_class text NOT NULL,
  quantity numeric(18, 6) NOT NULL,
  average_price numeric(18, 6) NOT NULL,
  updated_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT uq_paper_positions_account_symbol_asset UNIQUE (account_id, symbol, asset_class)
);

CREATE TABLE IF NOT EXISTS paper_audit_events (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  actor_type text NOT NULL,
  resource_type text NOT NULL,
  resource_id uuid NOT NULL,
  action text NOT NULL,
  outcome text NOT NULL,
  reason_code text NOT NULL,
  message text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);
```

Append these indexes to the final index section:

```sql
CREATE INDEX IF NOT EXISTS idx_paper_accounts_status ON paper_accounts(status);
CREATE INDEX IF NOT EXISTS idx_paper_order_intents_account_created ON paper_order_intents(account_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_paper_order_intents_status ON paper_order_intents(status);
CREATE INDEX IF NOT EXISTS idx_paper_risk_decisions_intent_created ON paper_risk_decisions(intent_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_paper_fills_intent_filled ON paper_fills(intent_id, filled_at ASC);
CREATE INDEX IF NOT EXISTS idx_paper_positions_account_symbol ON paper_positions(account_id, symbol);
CREATE INDEX IF NOT EXISTS idx_paper_audit_events_resource_created ON paper_audit_events(resource_id, created_at ASC);
```

- [ ] **Step 2: Run static SQL grep check**

Run:

```bash
rg -n "CREATE TABLE IF NOT EXISTS paper_|idx_paper_" backend/app/db/schema.sql
```

Expected: all six table definitions and seven indexes are listed.

## Task 5: Run Safety Grep and Backend Regression

**Files:**
- No file changes.

- [ ] **Step 1: Confirm no broker or live execution implementation was introduced**

Run:

```bash
rg -n "broker|live execution|place_order|submit_order|ibkr|alpaca|order_id|account_number|requests\\.|httpx|aiohttp" backend/app/paper_trading backend/tests/test_paper_trading_repository.py backend/app/db/models.py backend/app/db/schema.sql
```

Expected: no output. If implementation code contains broker routes, broker SDK names, live order ids, account numbers, or network libraries, stop and remove them.

- [ ] **Step 2: Run focused paper tests on Ubuntu**

```bash
ssh yasin-ubuntu 'cd /tmp/<slice4-clone>/backend && PYTHONPATH=. /home/yasin/workspace/TradingAgents/backend/.venv/bin/python -m pytest -q tests/test_paper_trading_contracts.py tests/test_paper_trading_risk_guard.py tests/test_paper_trading_repository.py --tb=short'
```

Expected: PASS.

- [ ] **Step 3: Run full backend regression on Ubuntu**

```bash
ssh yasin-ubuntu 'cd /tmp/<slice4-clone>/backend && PYTHONPATH=. /home/yasin/workspace/TradingAgents/backend/.venv/bin/python -m pytest -q --tb=short'
```

Expected: PASS.

## Task 6: Update Documentation After Verification

**Files:**
- Modify: `docs/roadmap/phase-5-roadmap.md`
- Modify: `PROJECT.md`

- [ ] **Step 1: Update Slice 4 status in the roadmap**

In `docs/roadmap/phase-5-roadmap.md`, replace:

```markdown
### Slice 4: Paper Persistence and Audit Log

Status: pending Slice 3.
```

with:

```markdown
### Slice 4: Paper Persistence and Audit Log

Status: implemented and validated on 2026-06-20.
```

Then add this under the Slice 4 heading:

```markdown
Implemented:

- Added SQLAlchemy models and SQL DDL for paper accounts, order intents, risk decisions, fills, positions, and audit events.
- Added `PaperTradingRepository` for contract-to-model persistence.
- Added append-only audit event insertion and resource-scoped audit listing.
- Added SQLite-backed repository tests for persistence and audit append behavior.
- Kept Slice 4 free of API routes, frontend UI, paper adapter execution, broker integration, live execution, network calls, and credential handling.
```

- [ ] **Step 2: Update project status snapshot**

In `PROJECT.md`, update the current Phase 5 state paragraph so it says Slice 4 paper persistence and append-only audit are implemented and validated, while APIs, adapter, UI, and broker execution remain out of scope.

Use this wording:

```markdown
- Current Phase 5 state: Phase 5 is in paper-only planning and early persistence implementation. Phase 4 completed the approved research-only Strategy Lab experiment workbench scope. Phase 5 now has paper-only architecture documentation, backend domain contracts, pure RiskGuard evaluator, SQLAlchemy persistence models, SQL schema, repository methods, and append-only audit event persistence for paper accounts/order intents/risk decisions/fills/positions/audit events. APIs, paper adapter execution, UI promotion flows, live broker execution, broker credentials, broker account mutation, AI-directed live trading, trading-scope MCP tools, and automatic paper-to-live promotion remain out of scope.
```

- [ ] **Step 3: Run docs diff check**

```bash
git diff -- docs/roadmap/phase-5-roadmap.md PROJECT.md
```

Expected: only Slice 4 status/evidence and project snapshot changes.

## Task 7: Final Verification, Commit, and Push

**Files:**
- Stage all files touched in this implementation.

- [ ] **Step 1: Run whitespace check**

```bash
git diff --check
```

Expected: no output.

- [ ] **Step 2: Run final focused paper tests on Ubuntu**

```bash
ssh yasin-ubuntu 'cd /tmp/<slice4-clone>/backend && PYTHONPATH=. /home/yasin/workspace/TradingAgents/backend/.venv/bin/python -m pytest -q tests/test_paper_trading_contracts.py tests/test_paper_trading_risk_guard.py tests/test_paper_trading_repository.py --tb=short'
```

Expected: PASS.

- [ ] **Step 3: Run final full backend regression on Ubuntu**

```bash
ssh yasin-ubuntu 'cd /tmp/<slice4-clone>/backend && PYTHONPATH=. /home/yasin/workspace/TradingAgents/backend/.venv/bin/python -m pytest -q --tb=short'
```

Expected: PASS.

- [ ] **Step 4: Stage implementation files**

```bash
git add backend/app/db/models.py backend/app/db/schema.sql backend/app/paper_trading/repository.py backend/tests/test_paper_trading_repository.py docs/roadmap/phase-5-roadmap.md PROJECT.md
```

- [ ] **Step 5: Commit**

```bash
git commit -m "feat: add paper trading persistence"
```

- [ ] **Step 6: Push**

```bash
git push origin aquantlens-us
```

## Self-Review Checklist

- Spec coverage: Slice 4 implements persistence and append-only audit only; API, UI, adapter, and broker work are deferred.
- Placeholder scan: this plan contains no placeholders for implementation behavior.
- Type consistency: table, model, repository, and contract names are consistent across tests and implementation.
- Safety boundary: implementation must not add broker credentials, live order ids, broker routes, broker SDK calls, network calls, API routes, frontend UI, or execution adapters.
