from datetime import datetime
from uuid import uuid4

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.paper_trading.adapter import (
    PaperExecutionError,
    cancel_paper_intent,
    execute_paper_intent,
)
from app.paper_trading.contracts import (
    AssetClass,
    OrderIntentStatus,
    OrderSide,
    OrderSource,
    OrderType,
    PaperAccount,
    PaperAccountStatus,
    PaperOrderIntent,
    PaperPosition,
    TimeInForce,
)
from app.paper_trading.repository import PaperTradingRepository


def test_paper_adapter_buys_and_updates_cash_position_fill_and_status():
    repository, account = repository_with_account()
    intent = paper_intent(account.account_id, side=OrderSide.BUY, quantity=2)
    repository.save_order_intent(intent)

    result = execute_paper_intent(repository, intent.intent_id, market_price=500, filled_at=timestamp())

    assert result.fill.fill_price == 500
    assert result.fill.quantity == 2
    assert result.account.current_cash == 99_000
    assert result.position.quantity == 2
    assert result.position.average_price == 500
    assert result.intent.status == OrderIntentStatus.PAPER_FILLED
    assert repository.list_fills_for_intent(intent.intent_id) == [result.fill]
    assert repository.list_audit_events(intent.intent_id)[-1].reason_code == "paper_filled"


def test_paper_adapter_buys_existing_position_with_weighted_average():
    repository, account = repository_with_account()
    repository.save_position(
        PaperPosition(
            position_id=uuid4(),
            account_id=account.account_id,
            symbol="SPY",
            asset_class=AssetClass.ETF,
            quantity=2,
            average_price=400,
            updated_at=timestamp(),
        )
    )
    intent = paper_intent(account.account_id, side=OrderSide.BUY, quantity=2)
    repository.save_order_intent(intent)

    result = execute_paper_intent(repository, intent.intent_id, market_price=600, filled_at=timestamp())

    assert result.account.current_cash == 98_800
    assert result.position.quantity == 4
    assert result.position.average_price == 500


def test_paper_adapter_sells_existing_position_and_updates_cash():
    repository, account = repository_with_account()
    repository.save_position(
        PaperPosition(
            position_id=uuid4(),
            account_id=account.account_id,
            symbol="SPY",
            asset_class=AssetClass.ETF,
            quantity=3,
            average_price=450,
            updated_at=timestamp(),
        )
    )
    intent = paper_intent(account.account_id, side=OrderSide.SELL, quantity=1)
    repository.save_order_intent(intent)

    result = execute_paper_intent(repository, intent.intent_id, market_price=500, filled_at=timestamp())

    assert result.account.current_cash == 100_500
    assert result.position.quantity == 2
    assert result.position.average_price == 450
    assert result.intent.status == OrderIntentStatus.PAPER_FILLED


def test_paper_adapter_rejects_buy_when_cash_is_insufficient():
    repository, account = repository_with_account(current_cash=100)
    intent = paper_intent(account.account_id, side=OrderSide.BUY, quantity=1)
    repository.save_order_intent(intent)

    with pytest.raises(PaperExecutionError, match="insufficient_cash"):
        execute_paper_intent(repository, intent.intent_id, market_price=500, filled_at=timestamp())

    assert repository.get_account(account.account_id).current_cash == 100
    assert repository.get_order_intent(intent.intent_id).status == OrderIntentStatus.APPROVED_FOR_PAPER
    assert repository.list_fills_for_intent(intent.intent_id) == []
    assert repository.list_audit_events(intent.intent_id)[-1].reason_code == "insufficient_cash"


def test_paper_adapter_rejects_sell_without_enough_position():
    repository, account = repository_with_account()
    intent = paper_intent(account.account_id, side=OrderSide.SELL, quantity=1)
    repository.save_order_intent(intent)

    with pytest.raises(PaperExecutionError, match="insufficient_position"):
        execute_paper_intent(repository, intent.intent_id, market_price=500, filled_at=timestamp())

    assert repository.get_account(account.account_id).current_cash == 100_000
    assert repository.list_fills_for_intent(intent.intent_id) == []
    assert repository.list_audit_events(intent.intent_id)[-1].reason_code == "insufficient_position"


def test_paper_adapter_rejects_intent_that_is_not_approved_for_paper():
    repository, account = repository_with_account()
    intent = paper_intent(account.account_id, status=OrderIntentStatus.AWAITING_REVIEW)
    repository.save_order_intent(intent)

    with pytest.raises(PaperExecutionError, match="intent_not_approved_for_paper"):
        execute_paper_intent(repository, intent.intent_id, market_price=500, filled_at=timestamp())

    assert repository.list_fills_for_intent(intent.intent_id) == []


def test_paper_adapter_cancels_unfilled_intent():
    repository, account = repository_with_account()
    intent = paper_intent(account.account_id, status=OrderIntentStatus.APPROVED_FOR_PAPER)
    repository.save_order_intent(intent)

    result = cancel_paper_intent(repository, intent.intent_id, message="Human cancelled paper intent.")

    assert result.intent.status == OrderIntentStatus.PAPER_CANCELLED
    assert repository.list_audit_events(intent.intent_id)[-1].reason_code == "paper_cancelled"


def test_paper_adapter_rejects_cancel_after_fill():
    repository, account = repository_with_account()
    intent = paper_intent(account.account_id, status=OrderIntentStatus.PAPER_FILLED)
    repository.save_order_intent(intent)

    with pytest.raises(PaperExecutionError, match="intent_cannot_be_cancelled"):
        cancel_paper_intent(repository, intent.intent_id, message="Too late.")


def test_paper_adapter_does_not_use_broker_network_or_live_execution_fields():
    import app.paper_trading.adapter as adapter

    public_names = " ".join(name.lower() for name in dir(adapter))
    assert "broker" not in public_names
    assert "live" not in public_names
    assert "requests" not in public_names
    assert "httpx" not in public_names
    assert "aiohttp" not in public_names


def repository_with_account(current_cash=100_000):
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    repository = PaperTradingRepository(session)
    account = PaperAccount(
        account_id=uuid4(),
        name="Simulation account",
        base_currency="USD",
        starting_cash=100_000,
        current_cash=current_cash,
        status=PaperAccountStatus.ACTIVE,
        created_at=timestamp(),
    )
    repository.save_account(account)
    return repository, account


def paper_intent(
    account_id,
    *,
    side=OrderSide.BUY,
    quantity=1,
    status=OrderIntentStatus.APPROVED_FOR_PAPER,
    order_type=OrderType.MARKET,
    limit_price=None,
    asset_class=AssetClass.ETF,
):
    return PaperOrderIntent(
        intent_id=uuid4(),
        account_id=account_id,
        source=OrderSource.HUMAN,
        source_reference_id=uuid4(),
        symbol="SPY",
        asset_class=asset_class,
        side=side,
        quantity=quantity,
        order_type=order_type,
        limit_price=limit_price,
        time_in_force=TimeInForce.DAY,
        status=status,
        idempotency_key=f"paper-adapter-{uuid4()}",
        created_at=timestamp(),
    )


def timestamp():
    return datetime(2026, 6, 20, 14, 30)
