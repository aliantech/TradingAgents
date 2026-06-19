from uuid import uuid4

from app.paper_trading.contracts import (
    AssetClass,
    OrderType,
    PaperAccountStatus,
    PaperOrderIntent,
    RiskDecision,
    RiskDecisionResult,
    RiskGuardInput,
)


OPTION_ASSET_CLASSES = {AssetClass.INDEX_OPTION, AssetClass.EQUITY_OPTION}
FALLBACK_MARKET_PRICE = 500
OPTION_CONTRACT_MULTIPLIER = 100


def evaluate_order_intent(risk_input: RiskGuardInput) -> RiskDecision:
    intent = risk_input.intent
    estimated_notional = estimate_notional(risk_input)

    if risk_input.account.status != PaperAccountStatus.ACTIVE:
        return reject(intent, "paper_account_inactive", estimated_notional)
    if intent.symbol not in risk_input.allowed_symbols:
        return reject(intent, "symbol_not_allowlisted", estimated_notional)
    if intent.asset_class not in risk_input.allowed_asset_classes:
        return reject(intent, "asset_class_not_allowed", estimated_notional)
    if intent.quantity <= 0:
        return reject(intent, "quantity_not_positive", estimated_notional)
    if intent.order_type == OrderType.LIMIT and (intent.limit_price is None or intent.limit_price <= 0):
        return reject(intent, "limit_price_not_positive", estimated_notional)
    if estimated_notional > risk_input.limits.max_notional_per_intent:
        return reject(intent, "estimated_notional_exceeds_intent_limit", estimated_notional)
    if (
        risk_input.limits.current_daily_notional + estimated_notional
        > risk_input.limits.max_daily_notional
    ):
        return reject(intent, "estimated_daily_notional_exceeds_limit", estimated_notional)
    if intent.asset_class in OPTION_ASSET_CLASSES and risk_input.option_metadata is None:
        return reject(intent, "option_metadata_required", estimated_notional)
    if intent.source_reference_id not in risk_input.candidate_experiment_ids:
        return reject(intent, "candidate_source_required", estimated_notional)

    return RiskDecision(
        decision_id=uuid4(),
        intent_id=intent.intent_id,
        result=RiskDecisionResult.PASS,
        reason_codes=["risk_checks_passed"],
        explanation="RiskGuard checks passed for paper simulation.",
        estimated_notional=estimated_notional,
        created_at=intent.created_at,
    )


def estimate_notional(risk_input: RiskGuardInput) -> float:
    intent = risk_input.intent
    multiplier = OPTION_CONTRACT_MULTIPLIER if intent.asset_class in OPTION_ASSET_CLASSES else 1
    if intent.order_type == OrderType.LIMIT and intent.limit_price is not None:
        return round(intent.quantity * intent.limit_price * multiplier, 4)
    return round(intent.quantity * FALLBACK_MARKET_PRICE * multiplier, 4)


def reject(intent: PaperOrderIntent, reason_code: str, estimated_notional: float) -> RiskDecision:
    return RiskDecision(
        decision_id=uuid4(),
        intent_id=intent.intent_id,
        result=RiskDecisionResult.REJECT,
        reason_codes=[reason_code],
        explanation=f"RiskGuard rejected paper intent: {reason_code}.",
        estimated_notional=estimated_notional,
        created_at=intent.created_at,
    )
