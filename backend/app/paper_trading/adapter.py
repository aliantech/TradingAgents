from dataclasses import dataclass
from datetime import datetime
from uuid import UUID, uuid4

from app.paper_trading.contracts import (
    AssetClass,
    AuditOutcome,
    AuditResourceType,
    OrderIntentStatus,
    OrderSide,
    OrderType,
    PaperAccount,
    PaperAuditEvent,
    PaperFill,
    PaperOrderIntent,
    PaperPosition,
)
from app.paper_trading.repository import PaperTradingRepository


OPTION_ASSET_CLASSES = {AssetClass.INDEX_OPTION, AssetClass.EQUITY_OPTION}
CANCELLABLE_STATUSES = {
    OrderIntentStatus.DRAFT,
    OrderIntentStatus.AWAITING_REVIEW,
    OrderIntentStatus.APPROVED_FOR_PAPER,
}


class PaperExecutionError(ValueError):
    pass


@dataclass(frozen=True)
class PaperExecutionResult:
    intent: PaperOrderIntent
    account: PaperAccount
    position: PaperPosition | None
    fill: PaperFill | None


def execute_paper_intent(
    repository: PaperTradingRepository,
    intent_id: UUID,
    *,
    market_price: float,
    filled_at: datetime,
) -> PaperExecutionResult:
    intent = require_intent(repository, intent_id)
    if intent.status != OrderIntentStatus.APPROVED_FOR_PAPER:
        raise PaperExecutionError("intent_not_approved_for_paper")
    if market_price <= 0:
        raise PaperExecutionError("market_price_not_positive")

    account = require_account(repository, intent.account_id)
    fill_price = resolve_fill_price(intent, market_price)
    notional = calculate_notional(intent, fill_price)

    if intent.side == OrderSide.BUY:
        if account.current_cash < notional:
            append_event(repository, intent.intent_id, "insufficient_cash", "Paper buy rejected: insufficient cash.", filled_at)
            raise PaperExecutionError("insufficient_cash")
        account = require_account_update(repository, account.account_id, round(account.current_cash - notional, 4))
        position = upsert_buy_position(repository, intent, fill_price, filled_at)
    else:
        position = repository.get_position_by_account_symbol_asset(intent.account_id, intent.symbol, intent.asset_class)
        if position is None or position.quantity < intent.quantity:
            append_event(
                repository,
                intent.intent_id,
                "insufficient_position",
                "Paper sell rejected: insufficient position.",
                filled_at,
            )
            raise PaperExecutionError("insufficient_position")
        account = require_account_update(repository, account.account_id, round(account.current_cash + notional, 4))
        position = upsert_sell_position(repository, intent, position, filled_at)

    fill = PaperFill(
        fill_id=uuid4(),
        intent_id=intent.intent_id,
        account_id=intent.account_id,
        symbol=intent.symbol,
        asset_class=intent.asset_class,
        side=intent.side,
        quantity=intent.quantity,
        fill_price=fill_price,
        filled_at=filled_at,
    )
    repository.save_fill(fill)
    updated_intent = require_status_update(repository, intent.intent_id, OrderIntentStatus.PAPER_FILLED)
    append_event(repository, intent.intent_id, "paper_filled", "Paper intent filled by local simulation.", filled_at)
    return PaperExecutionResult(intent=updated_intent, account=account, position=position, fill=fill)


def cancel_paper_intent(
    repository: PaperTradingRepository,
    intent_id: UUID,
    *,
    message: str,
    cancelled_at: datetime | None = None,
) -> PaperExecutionResult:
    intent = require_intent(repository, intent_id)
    if intent.status not in CANCELLABLE_STATUSES:
        raise PaperExecutionError("intent_cannot_be_cancelled")
    timestamp = cancelled_at or intent.created_at
    updated_intent = require_status_update(repository, intent.intent_id, OrderIntentStatus.PAPER_CANCELLED)
    append_event(repository, intent.intent_id, "paper_cancelled", message, timestamp, outcome=AuditOutcome.DENIED)
    return PaperExecutionResult(
        intent=updated_intent,
        account=require_account(repository, intent.account_id),
        position=None,
        fill=None,
    )


def resolve_fill_price(intent: PaperOrderIntent, market_price: float) -> float:
    if intent.order_type == OrderType.LIMIT:
        return require_price(intent.limit_price)
    return require_price(market_price)


def require_price(price: float | None) -> float:
    if price is None or price <= 0:
        raise PaperExecutionError("fill_price_not_positive")
    return price


def calculate_notional(intent: PaperOrderIntent, fill_price: float) -> float:
    return round(intent.quantity * fill_price * multiplier_for(intent.asset_class), 4)


def multiplier_for(asset_class: AssetClass) -> int:
    return 100 if asset_class in OPTION_ASSET_CLASSES else 1


def upsert_buy_position(
    repository: PaperTradingRepository,
    intent: PaperOrderIntent,
    fill_price: float,
    updated_at: datetime,
) -> PaperPosition:
    existing = repository.get_position_by_account_symbol_asset(intent.account_id, intent.symbol, intent.asset_class)
    if existing is None:
        position = PaperPosition(
            position_id=uuid4(),
            account_id=intent.account_id,
            symbol=intent.symbol,
            asset_class=intent.asset_class,
            quantity=intent.quantity,
            average_price=fill_price,
            updated_at=updated_at,
        )
    else:
        total_quantity = existing.quantity + intent.quantity
        average_price = ((existing.quantity * existing.average_price) + (intent.quantity * fill_price)) / total_quantity
        position = PaperPosition(
            position_id=existing.position_id,
            account_id=existing.account_id,
            symbol=existing.symbol,
            asset_class=existing.asset_class,
            quantity=total_quantity,
            average_price=round(average_price, 4),
            updated_at=updated_at,
        )
    return repository.save_position(position)


def upsert_sell_position(
    repository: PaperTradingRepository,
    intent: PaperOrderIntent,
    existing: PaperPosition,
    updated_at: datetime,
) -> PaperPosition:
    remaining_quantity = round(existing.quantity - intent.quantity, 8)
    position = PaperPosition(
        position_id=existing.position_id,
        account_id=existing.account_id,
        symbol=existing.symbol,
        asset_class=existing.asset_class,
        quantity=remaining_quantity,
        average_price=existing.average_price if remaining_quantity > 0 else 0,
        updated_at=updated_at,
    )
    return repository.save_position(position)


def require_intent(repository: PaperTradingRepository, intent_id: UUID) -> PaperOrderIntent:
    intent = repository.get_order_intent(intent_id)
    if intent is None:
        raise PaperExecutionError("paper_intent_not_found")
    return intent


def require_account(repository: PaperTradingRepository, account_id: UUID) -> PaperAccount:
    account = repository.get_account(account_id)
    if account is None:
        raise PaperExecutionError("paper_account_not_found")
    return account


def require_account_update(repository: PaperTradingRepository, account_id: UUID, current_cash: float) -> PaperAccount:
    account = repository.update_account_cash(account_id, current_cash)
    if account is None:
        raise PaperExecutionError("paper_account_not_found")
    return account


def require_status_update(
    repository: PaperTradingRepository,
    intent_id: UUID,
    status: OrderIntentStatus,
) -> PaperOrderIntent:
    intent = repository.update_order_intent_status(intent_id, status)
    if intent is None:
        raise PaperExecutionError("paper_intent_not_found")
    return intent


def append_event(
    repository: PaperTradingRepository,
    intent_id: UUID,
    reason_code: str,
    message: str,
    created_at: datetime,
    *,
    outcome: AuditOutcome = AuditOutcome.SUCCESS,
) -> PaperAuditEvent:
    return repository.append_audit_event(
        PaperAuditEvent(
            event_id=uuid4(),
            actor_type="human",
            resource_type=AuditResourceType.ORDER_INTENT,
            resource_id=intent_id,
            action="paper_simulation",
            outcome=outcome,
            reason_code=reason_code,
            message=message,
            created_at=created_at,
        )
    )
