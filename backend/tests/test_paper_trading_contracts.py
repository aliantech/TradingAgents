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


def test_order_intent_rejects_market_order_with_limit_price():
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
            limit_price=500.25,
            time_in_force=TimeInForce.DAY,
            status=OrderIntentStatus.DRAFT,
            idempotency_key="market-with-limit-price",
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


def timestamp():
    return datetime(2026, 6, 20, 13, 30, tzinfo=UTC)


@pytest.mark.parametrize("bad_value", [float("nan"), float("inf"), float("-inf")])
@pytest.mark.parametrize(
    ("model_class", "field_name", "base_kwargs"),
    [
        (
            PaperAccount,
            "starting_cash",
            {
                "account_id": uuid4(),
                "name": "Bad paper account",
                "base_currency": "USD",
                "starting_cash": 100_000,
                "current_cash": 100_000,
                "status": PaperAccountStatus.ACTIVE,
                "created_at": timestamp(),
            },
        ),
        (
            PaperAccount,
            "current_cash",
            {
                "account_id": uuid4(),
                "name": "Bad paper account",
                "base_currency": "USD",
                "starting_cash": 100_000,
                "current_cash": 100_000,
                "status": PaperAccountStatus.ACTIVE,
                "created_at": timestamp(),
            },
        ),
        (
            PaperOrderIntent,
            "quantity",
            {
                "intent_id": uuid4(),
                "account_id": uuid4(),
                "source": OrderSource.HUMAN,
                "source_reference_id": uuid4(),
                "symbol": "SPY",
                "asset_class": AssetClass.ETF,
                "side": OrderSide.BUY,
                "quantity": 1,
                "order_type": OrderType.MARKET,
                "time_in_force": TimeInForce.DAY,
                "status": OrderIntentStatus.DRAFT,
                "idempotency_key": "bad-order-quantity",
                "created_at": timestamp(),
            },
        ),
        (
            PaperOrderIntent,
            "limit_price",
            {
                "intent_id": uuid4(),
                "account_id": uuid4(),
                "source": OrderSource.HUMAN,
                "source_reference_id": uuid4(),
                "symbol": "SPY",
                "asset_class": AssetClass.ETF,
                "side": OrderSide.BUY,
                "quantity": 1,
                "order_type": OrderType.LIMIT,
                "limit_price": 500.25,
                "time_in_force": TimeInForce.DAY,
                "status": OrderIntentStatus.DRAFT,
                "idempotency_key": "bad-limit-price",
                "created_at": timestamp(),
            },
        ),
        (
            RiskDecision,
            "estimated_notional",
            {
                "decision_id": uuid4(),
                "intent_id": uuid4(),
                "result": RiskDecisionResult.REJECT,
                "reason_codes": ["notional_limit_exceeded"],
                "explanation": "Estimated notional exceeds paper account limit.",
                "estimated_notional": 125_000,
                "created_at": timestamp(),
            },
        ),
        (
            PaperFill,
            "quantity",
            {
                "fill_id": uuid4(),
                "intent_id": uuid4(),
                "account_id": uuid4(),
                "symbol": "SPY",
                "asset_class": AssetClass.ETF,
                "side": OrderSide.BUY,
                "quantity": 2,
                "fill_price": 500.25,
                "filled_at": timestamp(),
            },
        ),
        (
            PaperFill,
            "fill_price",
            {
                "fill_id": uuid4(),
                "intent_id": uuid4(),
                "account_id": uuid4(),
                "symbol": "SPY",
                "asset_class": AssetClass.ETF,
                "side": OrderSide.BUY,
                "quantity": 2,
                "fill_price": 500.25,
                "filled_at": timestamp(),
            },
        ),
        (
            PaperPosition,
            "quantity",
            {
                "position_id": uuid4(),
                "account_id": uuid4(),
                "symbol": "SPY",
                "asset_class": AssetClass.ETF,
                "quantity": 2,
                "average_price": 500.25,
                "updated_at": timestamp(),
            },
        ),
        (
            PaperPosition,
            "average_price",
            {
                "position_id": uuid4(),
                "account_id": uuid4(),
                "symbol": "SPY",
                "asset_class": AssetClass.ETF,
                "quantity": 2,
                "average_price": 500.25,
                "updated_at": timestamp(),
            },
        ),
    ],
)
def test_numeric_contract_fields_reject_non_finite_values(
    model_class,
    field_name,
    base_kwargs,
    bad_value,
):
    with pytest.raises(ValidationError):
        model_class(**{**base_kwargs, field_name: bad_value})


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


def test_paper_trading_package_exports_contracts():
    import app.paper_trading as paper_trading

    assert paper_trading.PaperAccount is PaperAccount
    assert paper_trading.PaperOrderIntent is PaperOrderIntent
    assert paper_trading.RiskDecision is RiskDecision
    assert paper_trading.PaperFill is PaperFill
    assert paper_trading.PaperPosition is PaperPosition
    assert paper_trading.PaperAuditEvent is PaperAuditEvent
