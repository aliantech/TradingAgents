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
    PaperAccount,
    PaperAccountStatus,
    PaperAuditEvent,
    PaperFill,
    PaperOrderIntent,
    PaperPosition,
    RiskDecision,
    RiskDecisionResult,
    RiskGuardInput,
    RiskGuardLimits,
    TimeInForce,
)
from app.paper_trading.adapter import PaperExecutionError, cancel_paper_intent, execute_paper_intent
from app.paper_trading.pnl import (
    PaperPnlSnapshot,
    ReferencePrice,
    calculate_paper_pnl_snapshot,
    calculate_realized_pnl,
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


class PaperSubmitRequest(BaseModel):
    market_price: float = Field(gt=0, allow_inf_nan=False)


class PaperCancelRequest(BaseModel):
    message: str = Field(min_length=1, max_length=500)


class PaperAccountCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    base_currency: str = Field(default="USD", min_length=3, max_length=3)
    starting_cash: float = Field(gt=0, allow_inf_nan=False)


class PaperAccountItem(BaseModel):
    account_id: UUID
    name: str
    base_currency: str
    starting_cash: float
    current_cash: float
    status: str
    created_at: str


class PaperAccountResponse(BaseModel):
    scope: str = "paper_only"
    account: PaperAccountItem


class PaperAccountListResponse(BaseModel):
    scope: str = "paper_only"
    accounts: list[PaperAccountItem]


class PaperPositionItem(BaseModel):
    position_id: UUID
    account_id: UUID
    symbol: str
    asset_class: str
    quantity: float
    average_price: float
    updated_at: str


class PaperFillItem(BaseModel):
    fill_id: UUID
    intent_id: UUID
    account_id: UUID
    symbol: str
    asset_class: str
    side: str
    quantity: float
    fill_price: float
    filled_at: str


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


class PaperAccountSummaryResponse(BaseModel):
    scope: str = "paper_only"
    account: PaperAccountItem
    positions: list[PaperPositionItem]
    recent_intents: list[PaperIntentItem]
    recent_fills: list[PaperFillItem]
    recent_audit_events: list[PaperAuditEventItem]


class PaperPnlSnapshotRequest(BaseModel):
    as_of: datetime | None = None
    max_price_age_seconds: int = Field(default=900, gt=0)
    reference_prices: list[ReferencePrice]


class PaperPnlSnapshotResponse(BaseModel):
    scope: str = "paper_only"
    snapshot: PaperPnlSnapshot


@router.get("/accounts", response_model=PaperAccountListResponse)
def list_paper_accounts(session: Session = Depends(get_db_session)):
    repository = PaperTradingRepository(session)
    return PaperAccountListResponse(accounts=[to_account_item(account) for account in repository.list_accounts()])


@router.post("/accounts", response_model=PaperAccountResponse, status_code=status.HTTP_201_CREATED)
def create_paper_account(
    request: PaperAccountCreateRequest,
    session: Session = Depends(get_db_session),
):
    account = PaperAccount(
        account_id=uuid4(),
        name=request.name,
        base_currency=request.base_currency.upper(),
        starting_cash=request.starting_cash,
        current_cash=request.starting_cash,
        status=PaperAccountStatus.ACTIVE,
        created_at=utc_now(),
    )
    repository = PaperTradingRepository(session)
    repository.save_account(account)
    return PaperAccountResponse(account=to_account_item(account))


@router.get("/accounts/{account_id}/summary", response_model=PaperAccountSummaryResponse)
def get_paper_account_summary(account_id: UUID, session: Session = Depends(get_db_session)):
    repository = PaperTradingRepository(session)
    account = repository.get_account(account_id)
    if account is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="paper account not found")
    return PaperAccountSummaryResponse(
        account=to_account_item(account),
        positions=[to_position_item(position) for position in repository.list_positions_for_account(account_id)],
        recent_intents=[to_intent_item(intent) for intent in repository.list_order_intents(account_id)],
        recent_fills=[to_fill_item(fill) for fill in repository.list_recent_fills_for_account(account_id)],
        recent_audit_events=[
            to_audit_item(event) for event in repository.list_recent_audit_events_for_account(account_id)
        ],
    )


@router.post("/accounts/{account_id}/pnl-snapshot", response_model=PaperPnlSnapshotResponse)
def create_paper_account_pnl_snapshot(
    account_id: UUID,
    request: PaperPnlSnapshotRequest,
    session: Session = Depends(get_db_session),
):
    repository = PaperTradingRepository(session)
    account = repository.get_account(account_id)
    if account is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="paper account not found")
    fills = repository.list_fills_for_account(account_id)
    snapshot = calculate_paper_pnl_snapshot(
        account=account,
        positions=repository.list_positions_for_account(account_id),
        reference_prices=request.reference_prices,
        as_of=request.as_of or utc_now(),
        max_price_age_seconds=request.max_price_age_seconds,
        realized_pnl=calculate_realized_pnl(fills),
    )
    return PaperPnlSnapshotResponse(snapshot=snapshot)


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


@router.post("/intents/{intent_id}/paper-submit", response_model=PaperIntentResponse)
def submit_paper_intent(
    intent_id: UUID,
    request: PaperSubmitRequest,
    session: Session = Depends(get_db_session),
):
    repository = PaperTradingRepository(session)
    try:
        result = execute_paper_intent(
            repository,
            intent_id,
            market_price=request.market_price,
            filled_at=utc_now(),
        )
    except PaperExecutionError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return build_response(repository, result.intent)


@router.post("/intents/{intent_id}/cancel", response_model=PaperIntentResponse)
def cancel_paper_intent_endpoint(
    intent_id: UUID,
    request: PaperCancelRequest,
    session: Session = Depends(get_db_session),
):
    repository = PaperTradingRepository(session)
    try:
        result = cancel_paper_intent(repository, intent_id, message=request.message, cancelled_at=utc_now())
    except PaperExecutionError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return build_response(repository, result.intent)


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


def to_account_item(account: PaperAccount) -> PaperAccountItem:
    return PaperAccountItem(
        account_id=account.account_id,
        name=account.name,
        base_currency=account.base_currency,
        starting_cash=account.starting_cash,
        current_cash=account.current_cash,
        status=account.status.value,
        created_at=account.created_at.isoformat(),
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


def to_position_item(position: PaperPosition) -> PaperPositionItem:
    return PaperPositionItem(
        position_id=position.position_id,
        account_id=position.account_id,
        symbol=position.symbol,
        asset_class=position.asset_class.value,
        quantity=position.quantity,
        average_price=position.average_price,
        updated_at=position.updated_at.isoformat(),
    )


def to_fill_item(fill: PaperFill) -> PaperFillItem:
    return PaperFillItem(
        fill_id=fill.fill_id,
        intent_id=fill.intent_id,
        account_id=fill.account_id,
        symbol=fill.symbol,
        asset_class=fill.asset_class.value,
        side=fill.side.value,
        quantity=fill.quantity,
        fill_price=fill.fill_price,
        filled_at=fill.filled_at.isoformat(),
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
