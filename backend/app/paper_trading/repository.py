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
