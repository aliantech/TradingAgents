from datetime import datetime, timedelta
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
    first = audit_event(resource_id, reason_code="created", seconds=0)
    second = audit_event(resource_id, reason_code="risk_passed", seconds=1)

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


def audit_event(resource_id, *, reason_code, seconds=0):
    return PaperAuditEvent(
        event_id=uuid4(),
        actor_type="human",
        resource_type=AuditResourceType.ORDER_INTENT,
        resource_id=resource_id,
        action="paper_transition",
        outcome=AuditOutcome.SUCCESS,
        reason_code=reason_code,
        message=f"Audit event: {reason_code}.",
        created_at=timestamp() + timedelta(seconds=seconds),
    )


def timestamp():
    return datetime(2026, 6, 20, 13, 30)
