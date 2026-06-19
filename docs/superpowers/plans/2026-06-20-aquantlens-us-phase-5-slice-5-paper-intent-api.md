# AQuantLens US Phase 5 Slice 5 Paper Intent API Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add human-facing paper intent API endpoints for draft creation, RiskGuard evaluation, listing, detail, and review approval/rejection without adding agent-facing trading scope, MCP trading tools, paper execution adapters, broker adapters, or live execution behavior.

**Architecture:** Add a new FastAPI router under `app.paper_trading.router` and mount it at `/api/paper-trading`. The router uses the existing `PaperTradingRepository`, `RiskGuard`, and SQLAlchemy session dependency. Intent creation is idempotent by `(account_id, idempotency_key)`, review actions only move intents between paper review states, and every API mutation appends a paper audit event.

**Tech Stack:** FastAPI, Pydantic v2, SQLAlchemy ORM, pytest, FastAPI `TestClient`, existing paper trading contracts/repository/RiskGuard.

---

## Scope

This plan implements Phase 5 Slice 5 only.

Included:

- Human-facing `/api/paper-trading` router.
- Draft paper intent creation.
- Idempotency-key replay for draft intent creation.
- Intent listing and detail.
- RiskGuard evaluation endpoint.
- Human approve/reject endpoint.
- Audit events for create, RiskGuard pass/reject, human approval, and human rejection.
- Focused API tests.
- Safety grep checks.
- Roadmap and project status updates.

Excluded:

- Agent Gateway write scope.
- MCP trading tools.
- Paper execution adapter.
- Fill or position mutation from API.
- Broker integration.
- Live execution.
- Broker credentials or account identifiers.
- Frontend UI.

## API Shape

Use these endpoints:

- `POST /api/paper-trading/intents`
- `GET /api/paper-trading/intents`
- `GET /api/paper-trading/intents/{intent_id}`
- `POST /api/paper-trading/intents/{intent_id}/risk-check`
- `POST /api/paper-trading/intents/{intent_id}/review`

Use header:

- `Idempotency-Key` for `POST /api/paper-trading/intents`.

Use statuses:

- `draft`
- `risk_rejected`
- `awaiting_review`
- `approved_for_paper`

Do not submit to paper adapter in Slice 5.

## File Structure

- Modify `backend/app/paper_trading/repository.py`
  - Add idempotency lookup, list intents, latest risk decision lookup, and intent status update.
- Create `backend/app/paper_trading/router.py`
  - Add paper intent API schemas and endpoints.
- Modify `backend/app/main.py`
  - Include the paper trading router.
- Create `backend/tests/test_paper_trading_api.py`
  - Add API tests for create/list/detail/idempotency/RiskGuard/review/safety.
- Modify `docs/roadmap/phase-5-roadmap.md`
  - Mark Slice 5 implemented after verification.
- Modify `PROJECT.md`
  - Update current Phase 5 state after verification.

## Task 1: Add Failing Paper Intent API Tests

**Files:**
- Create: `backend/tests/test_paper_trading_api.py`

- [ ] **Step 1: Write the failing API test file**

Create `backend/tests/test_paper_trading_api.py` with this content:

```python
from datetime import datetime
from uuid import uuid4

from fastapi.testclient import TestClient

from app.db.models import StrategyExperimentModel
from app.db.session import SessionLocal
from app.main import app
from app.paper_trading.contracts import PaperAccount, PaperAccountStatus
from app.paper_trading.repository import PaperTradingRepository


def test_paper_intent_api_creates_lists_and_reads_draft_intent():
    client = TestClient(app)
    account_id = seed_account()
    candidate_id = seed_candidate_experiment()

    create_response = client.post(
        "/api/paper-trading/intents",
        headers={"Idempotency-Key": "paper-intent-create-1"},
        json={
            "account_id": str(account_id),
            "source_reference_id": str(candidate_id),
            "symbol": "SPY",
            "asset_class": "etf",
            "side": "buy",
            "quantity": 2,
            "order_type": "market",
            "time_in_force": "day",
        },
    )

    assert create_response.status_code == 201
    created = create_response.json()
    assert created["scope"] == "paper_only"
    assert created["intent"]["account_id"] == str(account_id)
    assert created["intent"]["symbol"] == "SPY"
    assert created["intent"]["status"] == "draft"
    assert created["latest_risk_decision"] is None
    assert created["audit_events"][-1]["reason_code"] == "intent_created"

    list_response = client.get("/api/paper-trading/intents", params={"account_id": str(account_id)})
    assert list_response.status_code == 200
    assert [row["intent_id"] for row in list_response.json()["intents"]] == [created["intent"]["intent_id"]]

    detail_response = client.get(f"/api/paper-trading/intents/{created['intent']['intent_id']}")
    assert detail_response.status_code == 200
    assert detail_response.json()["intent"] == created["intent"]


def test_paper_intent_create_requires_idempotency_key():
    client = TestClient(app)
    account_id = seed_account()
    candidate_id = seed_candidate_experiment()

    response = client.post(
        "/api/paper-trading/intents",
        json={
            "account_id": str(account_id),
            "source_reference_id": str(candidate_id),
            "symbol": "SPY",
            "asset_class": "etf",
            "side": "buy",
            "quantity": 1,
            "order_type": "market",
            "time_in_force": "day",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Idempotency-Key header is required"


def test_paper_intent_create_replays_idempotency_key():
    client = TestClient(app)
    account_id = seed_account()
    candidate_id = seed_candidate_experiment()
    payload = {
        "account_id": str(account_id),
        "source_reference_id": str(candidate_id),
        "symbol": "SPY",
        "asset_class": "etf",
        "side": "buy",
        "quantity": 1,
        "order_type": "market",
        "time_in_force": "day",
    }

    first = client.post(
        "/api/paper-trading/intents",
        headers={"Idempotency-Key": "paper-intent-replay-1"},
        json=payload,
    )
    second = client.post(
        "/api/paper-trading/intents",
        headers={"Idempotency-Key": "paper-intent-replay-1"},
        json=payload,
    )

    assert first.status_code == 201
    assert second.status_code == 200
    assert second.json()["intent"]["intent_id"] == first.json()["intent"]["intent_id"]
    assert second.json()["replayed"] is True


def test_paper_intent_api_runs_riskguard_and_sets_review_status():
    client = TestClient(app)
    account_id = seed_account()
    candidate_id = seed_candidate_experiment()
    intent_id = create_intent(client, account_id, candidate_id)

    response = client.post(
        f"/api/paper-trading/intents/{intent_id}/risk-check",
        json={
            "allowed_symbols": ["SPY"],
            "allowed_asset_classes": ["etf"],
            "max_notional_per_intent": 2_000,
            "max_daily_notional": 5_000,
            "current_daily_notional": 0,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["intent"]["status"] == "awaiting_review"
    assert body["latest_risk_decision"]["result"] == "pass"
    assert body["latest_risk_decision"]["reason_codes"] == ["risk_checks_passed"]
    assert body["audit_events"][-1]["reason_code"] == "risk_checks_passed"


def test_paper_intent_api_records_risk_rejection():
    client = TestClient(app)
    account_id = seed_account()
    candidate_id = seed_candidate_experiment()
    intent_id = create_intent(client, account_id, candidate_id)

    response = client.post(
        f"/api/paper-trading/intents/{intent_id}/risk-check",
        json={
            "allowed_symbols": ["QQQ"],
            "allowed_asset_classes": ["etf"],
            "max_notional_per_intent": 2_000,
            "max_daily_notional": 5_000,
            "current_daily_notional": 0,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["intent"]["status"] == "risk_rejected"
    assert body["latest_risk_decision"]["result"] == "reject"
    assert body["latest_risk_decision"]["reason_codes"] == ["symbol_not_allowlisted"]


def test_paper_intent_api_requires_risk_pass_before_approval():
    client = TestClient(app)
    account_id = seed_account()
    candidate_id = seed_candidate_experiment()
    intent_id = create_intent(client, account_id, candidate_id)

    response = client.post(
        f"/api/paper-trading/intents/{intent_id}/review",
        json={"decision": "approve", "message": "Looks good for paper review."},
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "intent must pass RiskGuard before approval"


def test_paper_intent_api_approves_and_rejects_after_review():
    client = TestClient(app)
    account_id = seed_account()
    candidate_id = seed_candidate_experiment()
    approved_intent_id = create_intent(client, account_id, candidate_id, key="approve-flow")
    rejected_intent_id = create_intent(client, account_id, candidate_id, key="reject-flow")

    run_passing_risk_check(client, approved_intent_id)
    approve_response = client.post(
        f"/api/paper-trading/intents/{approved_intent_id}/review",
        json={"decision": "approve", "message": "Approved for paper simulation."},
    )
    assert approve_response.status_code == 200
    assert approve_response.json()["intent"]["status"] == "approved_for_paper"
    assert approve_response.json()["audit_events"][-1]["reason_code"] == "human_approved"

    run_passing_risk_check(client, rejected_intent_id)
    reject_response = client.post(
        f"/api/paper-trading/intents/{rejected_intent_id}/review",
        json={"decision": "reject", "message": "Rejecting this paper idea."},
    )
    assert reject_response.status_code == 200
    assert reject_response.json()["intent"]["status"] == "risk_rejected"
    assert reject_response.json()["audit_events"][-1]["reason_code"] == "human_rejected"


def test_paper_intent_api_does_not_expose_broker_or_live_fields():
    client = TestClient(app)
    account_id = seed_account()
    candidate_id = seed_candidate_experiment()
    intent_id = create_intent(client, account_id, candidate_id)

    response = client.get(f"/api/paper-trading/intents/{intent_id}")

    text = response.text.lower()
    assert "broker" not in text
    assert "live" not in text
    assert "order_id" not in text


def seed_account():
    session = SessionLocal()
    try:
        account = PaperAccount(
            account_id=uuid4(),
            name="API paper account",
            base_currency="USD",
            starting_cash=100_000,
            current_cash=100_000,
            status=PaperAccountStatus.ACTIVE,
            created_at=timestamp(),
        )
        PaperTradingRepository(session).save_account(account)
        return account.account_id
    finally:
        session.close()


def seed_candidate_experiment():
    session = SessionLocal()
    try:
        experiment = StrategyExperimentModel(
            title="SPY paper candidate",
            symbol="SPY",
            strategy_id="ma-cross-research",
            scope="research_only",
            parameters={"fast_window": 2, "slow_window": 3},
            preview_json={"backtest": {"return_pct": 1.2}},
            review_status="candidate",
        )
        session.add(experiment)
        session.commit()
        session.refresh(experiment)
        return experiment.id
    finally:
        session.close()


def create_intent(client, account_id, candidate_id, key="paper-api-intent"):
    response = client.post(
        "/api/paper-trading/intents",
        headers={"Idempotency-Key": key},
        json={
            "account_id": str(account_id),
            "source_reference_id": str(candidate_id),
            "symbol": "SPY",
            "asset_class": "etf",
            "side": "buy",
            "quantity": 2,
            "order_type": "market",
            "time_in_force": "day",
        },
    )
    assert response.status_code in {200, 201}
    return response.json()["intent"]["intent_id"]


def run_passing_risk_check(client, intent_id):
    response = client.post(
        f"/api/paper-trading/intents/{intent_id}/risk-check",
        json={
            "allowed_symbols": ["SPY"],
            "allowed_asset_classes": ["etf"],
            "max_notional_per_intent": 2_000,
            "max_daily_notional": 5_000,
            "current_daily_notional": 0,
        },
    )
    assert response.status_code == 200


def timestamp():
    return datetime(2026, 6, 20, 13, 30)
```

- [ ] **Step 2: Run the focused test and verify it fails for missing router**

Run on Ubuntu temporary clone:

```bash
ssh yasin-ubuntu 'cd /tmp/<slice5-clone>/backend && PYTHONPATH=. /home/yasin/workspace/TradingAgents/backend/.venv/bin/python -m pytest -q tests/test_paper_trading_api.py --tb=short'
```

Expected: FAIL with 404 responses for `/api/paper-trading/intents`.

## Task 2: Add Repository Helpers for API Workflows

**Files:**
- Modify: `backend/app/paper_trading/repository.py`
- Test: `backend/tests/test_paper_trading_api.py`

- [ ] **Step 1: Add helper methods to `PaperTradingRepository`**

Add these methods inside `PaperTradingRepository`:

```python
    def get_intent_by_idempotency_key(self, account_id: UUID, idempotency_key: str) -> PaperOrderIntent | None:
        model = self.session.scalar(
            select(PaperOrderIntentModel)
            .where(PaperOrderIntentModel.account_id == account_id)
            .where(PaperOrderIntentModel.idempotency_key == idempotency_key)
        )
        return to_order_intent(model) if model else None

    def list_order_intents(self, account_id: UUID | None = None) -> list[PaperOrderIntent]:
        statement = select(PaperOrderIntentModel).order_by(PaperOrderIntentModel.created_at.desc())
        if account_id is not None:
            statement = statement.where(PaperOrderIntentModel.account_id == account_id)
        return [to_order_intent(model) for model in self.session.scalars(statement.limit(100)).all()]

    def list_risk_decisions_for_intent(self, intent_id: UUID) -> list[RiskDecision]:
        models = self.session.scalars(
            select(PaperRiskDecisionModel)
            .where(PaperRiskDecisionModel.intent_id == intent_id)
            .order_by(PaperRiskDecisionModel.created_at.desc())
        ).all()
        return [to_risk_decision(model) for model in models]

    def get_latest_risk_decision(self, intent_id: UUID) -> RiskDecision | None:
        decisions = self.list_risk_decisions_for_intent(intent_id)
        return decisions[0] if decisions else None

    def update_order_intent_status(self, intent_id: UUID, status: OrderIntentStatus) -> PaperOrderIntent | None:
        model = self.session.get(PaperOrderIntentModel, intent_id)
        if model is None:
            return None
        model.status = status.value
        self.session.commit()
        self.session.refresh(model)
        return to_order_intent(model)
```

- [ ] **Step 2: Run the focused API test and verify it still fails for missing router**

Run:

```bash
ssh yasin-ubuntu 'cd /tmp/<slice5-clone>/backend && PYTHONPATH=. /home/yasin/workspace/TradingAgents/backend/.venv/bin/python -m pytest -q tests/test_paper_trading_api.py --tb=short'
```

Expected: FAIL with 404 responses for `/api/paper-trading/intents`.

## Task 3: Add Paper Trading API Router

**Files:**
- Create: `backend/app/paper_trading/router.py`
- Modify: `backend/app/main.py`
- Test: `backend/tests/test_paper_trading_api.py`

- [ ] **Step 1: Create `backend/app/paper_trading/router.py`**

Create `backend/app/paper_trading/router.py` with this implementation:

```python
from datetime import datetime
from typing import Literal
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import StrategyExperimentModel
from app.db.session import get_db_session
from app.paper_trading.contracts import (
    AssetClass,
    AuditOutcome,
    AuditResourceType,
    OrderIntentStatus,
    OrderSide,
    OrderSource,
    OrderType,
    PaperAuditEvent,
    PaperOrderIntent,
    RiskDecision,
    RiskDecisionResult,
    RiskGuardInput,
    RiskGuardLimits,
    TimeInForce,
)
from app.paper_trading.repository import PaperTradingRepository
from app.paper_trading.risk_guard import evaluate_order_intent


router = APIRouter(prefix="/api/paper-trading", tags=["paper-trading"])


class PaperIntentCreateRequest(BaseModel):
    account_id: UUID
    source_reference_id: UUID
    symbol: str = Field(min_length=1, max_length=64)
    asset_class: AssetClass
    side: OrderSide
    quantity: float = Field(gt=0, allow_inf_nan=False)
    order_type: OrderType
    limit_price: float | None = Field(default=None, gt=0, allow_inf_nan=False)
    time_in_force: TimeInForce


class PaperRiskCheckRequest(BaseModel):
    allowed_symbols: list[str] = Field(min_length=1)
    allowed_asset_classes: list[AssetClass] = Field(min_length=1)
    max_notional_per_intent: float = Field(gt=0, allow_inf_nan=False)
    max_daily_notional: float = Field(gt=0, allow_inf_nan=False)
    current_daily_notional: float = Field(ge=0, allow_inf_nan=False)


class PaperReviewRequest(BaseModel):
    decision: Literal["approve", "reject"]
    message: str = Field(min_length=1, max_length=500)


class PaperIntentItem(BaseModel):
    intent_id: UUID
    account_id: UUID
    source: str
    source_reference_id: UUID
    symbol: str
    asset_class: str
    side: str
    quantity: float
    order_type: str
    limit_price: float | None = None
    time_in_force: str
    status: str
    idempotency_key: str
    created_at: str


class PaperRiskDecisionItem(BaseModel):
    decision_id: UUID
    intent_id: UUID
    result: str
    reason_codes: list[str]
    explanation: str
    estimated_notional: float
    created_at: str


class PaperAuditEventItem(BaseModel):
    event_id: UUID
    actor_type: str
    resource_type: str
    resource_id: UUID
    action: str
    outcome: str
    reason_code: str
    message: str
    created_at: str


class PaperIntentResponse(BaseModel):
    scope: str = "paper_only"
    replayed: bool = False
    intent: PaperIntentItem
    latest_risk_decision: PaperRiskDecisionItem | None = None
    audit_events: list[PaperAuditEventItem]


class PaperIntentListResponse(BaseModel):
    scope: str = "paper_only"
    intents: list[PaperIntentItem]


@router.post("/intents", response_model=PaperIntentResponse)
def create_paper_intent(
    request: PaperIntentCreateRequest,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    session: Session = Depends(get_db_session),
):
    if not idempotency_key:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Idempotency-Key header is required")
    repository = PaperTradingRepository(session)
    existing = repository.get_intent_by_idempotency_key(request.account_id, idempotency_key)
    if existing is not None:
        return build_response(repository, existing, replayed=True)

    account = repository.get_account(request.account_id)
    if account is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="paper account not found")

    now = datetime.utcnow()
    intent = PaperOrderIntent(
        intent_id=uuid4(),
        account_id=request.account_id,
        source=OrderSource.HUMAN,
        source_reference_id=request.source_reference_id,
        symbol=request.symbol.upper(),
        asset_class=request.asset_class,
        side=request.side,
        quantity=request.quantity,
        order_type=request.order_type,
        limit_price=request.limit_price,
        time_in_force=request.time_in_force,
        status=OrderIntentStatus.DRAFT,
        idempotency_key=idempotency_key,
        created_at=now,
    )
    repository.save_order_intent(intent)
    repository.append_audit_event(
        audit_event(intent.intent_id, "intent_created", "Paper intent draft created.", created_at=now)
    )
    return build_response(repository, intent, status_code=status.HTTP_201_CREATED)


@router.get("/intents", response_model=PaperIntentListResponse)
def list_paper_intents(
    account_id: UUID | None = None,
    session: Session = Depends(get_db_session),
):
    repository = PaperTradingRepository(session)
    return PaperIntentListResponse(
        intents=[to_intent_item(intent) for intent in repository.list_order_intents(account_id)]
    )


@router.get("/intents/{intent_id}", response_model=PaperIntentResponse)
def get_paper_intent(intent_id: UUID, session: Session = Depends(get_db_session)):
    repository = PaperTradingRepository(session)
    intent = repository.get_order_intent(intent_id)
    if intent is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="paper intent not found")
    return build_response(repository, intent)


@router.post("/intents/{intent_id}/risk-check", response_model=PaperIntentResponse)
def run_paper_intent_risk_check(
    intent_id: UUID,
    request: PaperRiskCheckRequest,
    session: Session = Depends(get_db_session),
):
    repository = PaperTradingRepository(session)
    intent = repository.get_order_intent(intent_id)
    if intent is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="paper intent not found")
    account = repository.get_account(intent.account_id)
    if account is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="paper account not found")
    candidate_ids = set(
        session.scalars(
            select(StrategyExperimentModel.id)
            .where(StrategyExperimentModel.review_status == "candidate")
            .where(StrategyExperimentModel.archived.is_(False))
        ).all()
    )
    decision = evaluate_order_intent(
        RiskGuardInput(
            account=account,
            intent=intent,
            allowed_symbols={symbol.upper() for symbol in request.allowed_symbols},
            allowed_asset_classes=set(request.allowed_asset_classes),
            limits=RiskGuardLimits(
                max_notional_per_intent=request.max_notional_per_intent,
                max_daily_notional=request.max_daily_notional,
                current_daily_notional=request.current_daily_notional,
            ),
            candidate_experiment_ids=candidate_ids,
        )
    )
    repository.save_risk_decision(decision)
    next_status = (
        OrderIntentStatus.AWAITING_REVIEW
        if decision.result == RiskDecisionResult.PASS
        else OrderIntentStatus.RISK_REJECTED
    )
    updated = repository.update_order_intent_status(intent.intent_id, next_status)
    repository.append_audit_event(
        audit_event(intent.intent_id, decision.reason_codes[0], decision.explanation, created_at=decision.created_at)
    )
    return build_response(repository, updated)


@router.post("/intents/{intent_id}/review", response_model=PaperIntentResponse)
def review_paper_intent(
    intent_id: UUID,
    request: PaperReviewRequest,
    session: Session = Depends(get_db_session),
):
    repository = PaperTradingRepository(session)
    intent = repository.get_order_intent(intent_id)
    if intent is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="paper intent not found")
    latest_decision = repository.get_latest_risk_decision(intent.intent_id)
    if request.decision == "approve":
        if latest_decision is None or latest_decision.result != RiskDecisionResult.PASS:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="intent must pass RiskGuard before approval",
            )
        next_status = OrderIntentStatus.APPROVED_FOR_PAPER
        reason_code = "human_approved"
    else:
        next_status = OrderIntentStatus.RISK_REJECTED
        reason_code = "human_rejected"

    updated = repository.update_order_intent_status(intent.intent_id, next_status)
    repository.append_audit_event(audit_event(intent.intent_id, reason_code, request.message))
    return build_response(repository, updated)


def build_response(
    repository: PaperTradingRepository,
    intent: PaperOrderIntent,
    *,
    replayed: bool = False,
    status_code: int | None = None,
) -> PaperIntentResponse:
    response = PaperIntentResponse(
        replayed=replayed,
        intent=to_intent_item(intent),
        latest_risk_decision=to_decision_item(repository.get_latest_risk_decision(intent.intent_id)),
        audit_events=[to_audit_item(event) for event in repository.list_audit_events(intent.intent_id)],
    )
    return response


def audit_event(resource_id: UUID, reason_code: str, message: str, *, created_at: datetime | None = None) -> PaperAuditEvent:
    now = created_at or datetime.utcnow()
    outcome = AuditOutcome.SUCCESS if reason_code not in {"human_rejected"} else AuditOutcome.DENIED
    return PaperAuditEvent(
        event_id=uuid4(),
        actor_type="human",
        resource_type=AuditResourceType.ORDER_INTENT,
        resource_id=resource_id,
        action="paper_intent_transition",
        outcome=outcome,
        reason_code=reason_code,
        message=message,
        created_at=now,
    )


def to_intent_item(intent: PaperOrderIntent) -> PaperIntentItem:
    return PaperIntentItem(
        intent_id=intent.intent_id,
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
        created_at=intent.created_at.isoformat(),
    )


def to_decision_item(decision: RiskDecision | None) -> PaperRiskDecisionItem | None:
    if decision is None:
        return None
    return PaperRiskDecisionItem(
        decision_id=decision.decision_id,
        intent_id=decision.intent_id,
        result=decision.result.value,
        reason_codes=decision.reason_codes,
        explanation=decision.explanation,
        estimated_notional=decision.estimated_notional,
        created_at=decision.created_at.isoformat(),
    )


def to_audit_item(event: PaperAuditEvent) -> PaperAuditEventItem:
    return PaperAuditEventItem(
        event_id=event.event_id,
        actor_type=event.actor_type,
        resource_type=event.resource_type.value,
        resource_id=event.resource_id,
        action=event.action,
        outcome=event.outcome.value,
        reason_code=event.reason_code,
        message=event.message,
        created_at=event.created_at.isoformat(),
    )
```

- [ ] **Step 2: Return HTTP 201 for new intent creation**

The code above includes an unused `status_code` parameter in `build_response`. Replace the create endpoint decorator with:

```python
@router.post("/intents", response_model=PaperIntentResponse, status_code=status.HTTP_201_CREATED)
```

Then replace the replay branch:

```python
if existing is not None:
    return build_response(repository, existing, replayed=True)
```

with a response object that can return HTTP 200:

```python
if existing is not None:
    return build_response(repository, existing, replayed=True)
```

Keep the first implementation simple. If tests require exact 200 on replay, update with `Response.status_code = status.HTTP_200_OK`.

- [ ] **Step 3: Mount the router in `backend/app/main.py`**

Add import:

```python
from app.paper_trading.router import router as paper_trading_router
```

Add include after options or strategy lab:

```python
app.include_router(paper_trading_router)
```

- [ ] **Step 4: Run focused API tests**

Run:

```bash
ssh yasin-ubuntu 'cd /tmp/<slice5-clone>/backend && PYTHONPATH=. /home/yasin/workspace/TradingAgents/backend/.venv/bin/python -m pytest -q tests/test_paper_trading_api.py --tb=short'
```

Expected: API tests pass or reveal small HTTP status/serialization fixes.

## Task 4: Fix HTTP Replay Status and API Polish

**Files:**
- Modify: `backend/app/paper_trading/router.py`
- Test: `backend/tests/test_paper_trading_api.py`

- [ ] **Step 1: If idempotency replay returns 201, add explicit response status override**

Update create endpoint signature:

```python
from fastapi import APIRouter, Depends, Header, HTTPException, Response, status
```

and:

```python
def create_paper_intent(
    request: PaperIntentCreateRequest,
    response: Response,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    session: Session = Depends(get_db_session),
):
```

Inside replay branch:

```python
response.status_code = status.HTTP_200_OK
return build_response(repository, existing, replayed=True)
```

- [ ] **Step 2: Run focused API tests again**

Run:

```bash
ssh yasin-ubuntu 'cd /tmp/<slice5-clone>/backend && PYTHONPATH=. /home/yasin/workspace/TradingAgents/backend/.venv/bin/python -m pytest -q tests/test_paper_trading_api.py --tb=short'
```

Expected: PASS.

## Task 5: Run Safety Grep and Backend Regression

**Files:**
- No file changes.

- [ ] **Step 1: Confirm no broker or live execution implementation was introduced**

Run:

```bash
rg -n "broker|live execution|place_order|submit_order|ibkr|alpaca|order_id|account_number|requests\\.|httpx|aiohttp|MCP|agent scope|T scope" backend/app/paper_trading backend/tests/test_paper_trading_api.py backend/app/main.py
```

Expected: no output except negative test assertions. If implementation code contains broker routes, broker SDK names, live order ids, account numbers, network libraries, MCP trading tools, or agent trading scope, stop and remove them.

- [ ] **Step 2: Run focused paper tests on Ubuntu**

```bash
ssh yasin-ubuntu 'cd /tmp/<slice5-clone>/backend && PYTHONPATH=. /home/yasin/workspace/TradingAgents/backend/.venv/bin/python -m pytest -q tests/test_paper_trading_contracts.py tests/test_paper_trading_risk_guard.py tests/test_paper_trading_repository.py tests/test_paper_trading_api.py --tb=short'
```

Expected: PASS.

- [ ] **Step 3: Run full backend regression on Ubuntu**

```bash
ssh yasin-ubuntu 'cd /tmp/<slice5-clone>/backend && PYTHONPATH=. /home/yasin/workspace/TradingAgents/backend/.venv/bin/python -m pytest -q --tb=short'
```

Expected: PASS.

## Task 6: Update Documentation After Verification

**Files:**
- Modify: `docs/roadmap/phase-5-roadmap.md`
- Modify: `PROJECT.md`

- [ ] **Step 1: Update Slice 5 status in the roadmap**

In `docs/roadmap/phase-5-roadmap.md`, replace:

```markdown
### Slice 5: Paper Intent API

Status: pending Slice 4.
```

with:

```markdown
### Slice 5: Paper Intent API

Status: implemented and validated on 2026-06-20.
```

Then add:

```markdown
Implemented:

- Added human-facing `/api/paper-trading/intents` endpoints for draft creation, listing, detail, RiskGuard evaluation, and human review.
- Added idempotency-key replay for draft intent creation.
- Added audit records for intent creation, RiskGuard pass/reject, human approval, and human rejection.
- Kept agent-facing trading scope, MCP trading tools, paper adapter execution, broker integration, live execution, network calls, and credential handling out of scope.
```

- [ ] **Step 2: Update project status snapshot**

Use this wording in `PROJECT.md`:

```markdown
- Current Phase 5 state: Phase 5 is in paper-only planning and early API implementation. Phase 4 completed the approved research-only Strategy Lab experiment workbench scope. Phase 5 now has paper-only architecture documentation, backend domain contracts, pure RiskGuard evaluator, SQLAlchemy persistence, repository methods, append-only audit event persistence, and human-facing paper intent API endpoints for draft creation, RiskGuard evaluation, listing, detail, and review approval/rejection. Paper adapter execution, UI promotion flows, live broker execution, broker credentials, broker account mutation, AI-directed live trading, trading-scope MCP tools, and automatic paper-to-live promotion remain out of scope.
```

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
ssh yasin-ubuntu 'cd /tmp/<slice5-clone>/backend && PYTHONPATH=. /home/yasin/workspace/TradingAgents/backend/.venv/bin/python -m pytest -q tests/test_paper_trading_contracts.py tests/test_paper_trading_risk_guard.py tests/test_paper_trading_repository.py tests/test_paper_trading_api.py --tb=short'
```

Expected: PASS.

- [ ] **Step 3: Run final full backend regression on Ubuntu**

```bash
ssh yasin-ubuntu 'cd /tmp/<slice5-clone>/backend && PYTHONPATH=. /home/yasin/workspace/TradingAgents/backend/.venv/bin/python -m pytest -q --tb=short'
```

Expected: PASS.

- [ ] **Step 4: Stage implementation files**

```bash
git add backend/app/paper_trading/repository.py backend/app/paper_trading/router.py backend/app/main.py backend/tests/test_paper_trading_api.py docs/roadmap/phase-5-roadmap.md PROJECT.md
```

- [ ] **Step 5: Commit**

```bash
git commit -m "feat: add paper intent api"
```

- [ ] **Step 6: Push**

```bash
git push origin aquantlens-us
```

## Self-Review Checklist

- Spec coverage: Slice 5 implements human-facing paper intent API only; adapter, UI, agent write scope, and broker work are deferred.
- Placeholder scan: this plan contains no placeholders for implementation behavior.
- Type consistency: route names, schema fields, repository helper names, and reason codes are consistent across tests and implementation.
- Safety boundary: implementation must not add broker credentials, live order ids, broker routes, broker SDK calls, network calls, MCP trading tools, agent trading scope, frontend UI, or execution adapters.
