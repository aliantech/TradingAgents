from datetime import UTC, datetime
from typing import Literal
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, Header, HTTPException, Response, status
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


@router.post("/intents", response_model=PaperIntentResponse, status_code=status.HTTP_201_CREATED)
def create_paper_intent(
    request: PaperIntentCreateRequest,
    response: Response,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    session: Session = Depends(get_db_session),
):
    if not idempotency_key:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Idempotency-Key header is required")
    repository = PaperTradingRepository(session)
    existing = repository.get_intent_by_idempotency_key(request.account_id, idempotency_key)
    if existing is not None:
        response.status_code = status.HTTP_200_OK
        return build_response(repository, existing, replayed=True)

    account = repository.get_account(request.account_id)
    if account is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="paper account not found")

    now = utc_now()
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
    return build_response(repository, intent)


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
            candidate_experiment_ids=list_candidate_experiment_ids(session),
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
        audit_event(intent.intent_id, decision.reason_codes[0], decision.explanation)
    )
    return build_response(repository, require_intent(updated))


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
    return build_response(repository, require_intent(updated))


def list_candidate_experiment_ids(session: Session) -> set[UUID]:
    return set(
        session.scalars(
            select(StrategyExperimentModel.id)
            .where(StrategyExperimentModel.review_status == "candidate")
            .where(StrategyExperimentModel.archived.is_(False))
        ).all()
    )


def build_response(
    repository: PaperTradingRepository,
    intent: PaperOrderIntent,
    *,
    replayed: bool = False,
) -> PaperIntentResponse:
    return PaperIntentResponse(
        replayed=replayed,
        intent=to_intent_item(intent),
        latest_risk_decision=to_decision_item(repository.get_latest_risk_decision(intent.intent_id)),
        audit_events=[to_audit_item(event) for event in repository.list_audit_events(intent.intent_id)],
    )


def audit_event(
    resource_id: UUID,
    reason_code: str,
    message: str,
    *,
    created_at: datetime | None = None,
) -> PaperAuditEvent:
    return PaperAuditEvent(
        event_id=uuid4(),
        actor_type="human",
        resource_type=AuditResourceType.ORDER_INTENT,
        resource_id=resource_id,
        action="paper_intent_transition",
        outcome=AuditOutcome.DENIED if reason_code == "human_rejected" else AuditOutcome.SUCCESS,
        reason_code=reason_code,
        message=message,
        created_at=created_at or utc_now(),
    )


def utc_now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def require_intent(intent: PaperOrderIntent | None) -> PaperOrderIntent:
    if intent is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="paper intent not found")
    return intent


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
