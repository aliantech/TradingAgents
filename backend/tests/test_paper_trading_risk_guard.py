from datetime import UTC, date, datetime
from uuid import uuid4

from app.paper_trading.contracts import (
    AssetClass,
    OrderIntentStatus,
    OrderSide,
    OrderSource,
    OrderType,
    PaperAccount,
    PaperAccountStatus,
    PaperOrderIntent,
    RiskDecisionResult,
    RiskGuardInput,
    RiskGuardLimits,
    TimeInForce,
)
from app.paper_trading.risk_guard import evaluate_order_intent


def test_risk_guard_passes_valid_equity_intent():
    decision = evaluate_order_intent(
        RiskGuardInput(
            account=active_account(),
            intent=equity_intent(),
            allowed_symbols={"SPY"},
            allowed_asset_classes={AssetClass.ETF},
            limits=RiskGuardLimits(
                max_notional_per_intent=2_000,
                max_daily_notional=5_000,
                current_daily_notional=1_000,
            ),
            candidate_experiment_ids={SOURCE_REFERENCE_ID},
        )
    )

    assert decision.result == RiskDecisionResult.PASS
    assert decision.reason_codes == ["risk_checks_passed"]
    assert decision.estimated_notional == 1_000


def test_risk_guard_rejects_inactive_account():
    decision = evaluate_order_intent(
        base_input(account=active_account(status=PaperAccountStatus.PAUSED))
    )

    assert decision.result == RiskDecisionResult.REJECT
    assert decision.reason_codes == ["paper_account_inactive"]


def test_risk_guard_rejects_symbol_outside_allowlist():
    decision = evaluate_order_intent(base_input(allowed_symbols={"QQQ"}))

    assert decision.result == RiskDecisionResult.REJECT
    assert decision.reason_codes == ["symbol_not_allowlisted"]


def test_risk_guard_rejects_asset_class_outside_scope():
    decision = evaluate_order_intent(base_input(allowed_asset_classes={AssetClass.EQUITY}))

    assert decision.result == RiskDecisionResult.REJECT
    assert decision.reason_codes == ["asset_class_not_allowed"]


def test_risk_guard_rejects_non_positive_quantity_even_if_contract_was_bypassed():
    intent = equity_intent()
    object.__setattr__(intent, "quantity", 0)

    decision = evaluate_order_intent(base_input(intent=intent))

    assert decision.result == RiskDecisionResult.REJECT
    assert decision.reason_codes == ["quantity_not_positive"]
    assert decision.estimated_notional == 0


def test_risk_guard_rejects_non_positive_limit_price_even_if_contract_was_bypassed():
    intent = equity_intent(order_type=OrderType.LIMIT, limit_price=500)
    object.__setattr__(intent, "limit_price", 0)

    decision = evaluate_order_intent(base_input(intent=intent))

    assert decision.result == RiskDecisionResult.REJECT
    assert decision.reason_codes == ["limit_price_not_positive"]


def test_risk_guard_rejects_intent_notional_above_limit():
    decision = evaluate_order_intent(
        base_input(
            limits=RiskGuardLimits(
                max_notional_per_intent=999,
                max_daily_notional=5_000,
                current_daily_notional=0,
            )
        )
    )

    assert decision.result == RiskDecisionResult.REJECT
    assert decision.reason_codes == ["estimated_notional_exceeds_intent_limit"]
    assert decision.estimated_notional == 1_000


def test_risk_guard_rejects_daily_notional_above_limit():
    decision = evaluate_order_intent(
        base_input(
            limits=RiskGuardLimits(
                max_notional_per_intent=2_000,
                max_daily_notional=1_500,
                current_daily_notional=750,
            )
        )
    )

    assert decision.result == RiskDecisionResult.REJECT
    assert decision.reason_codes == ["estimated_daily_notional_exceeds_limit"]
    assert decision.estimated_notional == 1_000


def test_risk_guard_requires_option_metadata_for_option_intents():
    option_intent = equity_intent(
        symbol="SPY260620C00500000",
        asset_class=AssetClass.EQUITY_OPTION,
        order_type=OrderType.LIMIT,
        limit_price=5,
        quantity=1,
    )

    decision = evaluate_order_intent(
        base_input(
            intent=option_intent,
            allowed_symbols={"SPY260620C00500000"},
            allowed_asset_classes={AssetClass.EQUITY_OPTION},
            option_metadata=None,
        )
    )

    assert decision.result == RiskDecisionResult.REJECT
    assert decision.reason_codes == ["option_metadata_required"]


def test_risk_guard_passes_option_intent_with_metadata():
    option_intent = equity_intent(
        symbol="SPY260620C00500000",
        asset_class=AssetClass.EQUITY_OPTION,
        order_type=OrderType.LIMIT,
        limit_price=5,
        quantity=1,
    )

    decision = evaluate_order_intent(
        base_input(
            intent=option_intent,
            allowed_symbols={"SPY260620C00500000"},
            allowed_asset_classes={AssetClass.EQUITY_OPTION},
            option_metadata={
                "underlying_symbol": "SPY",
                "expiry": date(2026, 6, 20),
                "strike": 500,
                "option_type": "call",
            },
        )
    )

    assert decision.result == RiskDecisionResult.PASS
    assert decision.reason_codes == ["risk_checks_passed"]
    assert decision.estimated_notional == 500


def test_risk_guard_requires_candidate_source_reference():
    decision = evaluate_order_intent(base_input(candidate_experiment_ids=set()))

    assert decision.result == RiskDecisionResult.REJECT
    assert decision.reason_codes == ["candidate_source_required"]


def test_risk_guard_returns_first_deterministic_rejection():
    decision = evaluate_order_intent(
        base_input(
            account=active_account(status=PaperAccountStatus.PAUSED),
            allowed_symbols={"QQQ"},
        )
    )

    assert decision.result == RiskDecisionResult.REJECT
    assert decision.reason_codes == ["paper_account_inactive"]


def test_risk_guard_rejection_uses_intent_created_time():
    intent = equity_intent()

    decision = evaluate_order_intent(
        base_input(
            intent=intent,
            allowed_symbols={"QQQ"},
        )
    )

    assert decision.created_at == intent.created_at


SOURCE_REFERENCE_ID = uuid4()


def base_input(
    *,
    account=None,
    intent=None,
    allowed_symbols=None,
    allowed_asset_classes=None,
    limits=None,
    option_metadata=None,
    candidate_experiment_ids=None,
):
    return RiskGuardInput(
        account=account or active_account(),
        intent=intent or equity_intent(),
        allowed_symbols=allowed_symbols or {"SPY"},
        allowed_asset_classes=allowed_asset_classes or {AssetClass.ETF},
        limits=limits
        or RiskGuardLimits(
            max_notional_per_intent=2_000,
            max_daily_notional=5_000,
            current_daily_notional=1_000,
        ),
        option_metadata=option_metadata,
        candidate_experiment_ids=(
            {SOURCE_REFERENCE_ID}
            if candidate_experiment_ids is None
            else candidate_experiment_ids
        ),
    )


def active_account(status=PaperAccountStatus.ACTIVE):
    return PaperAccount(
        account_id=uuid4(),
        name="Default paper account",
        base_currency="USD",
        starting_cash=100_000,
        current_cash=100_000,
        status=status,
        created_at=timestamp(),
    )


def equity_intent(
    *,
    symbol="SPY",
    asset_class=AssetClass.ETF,
    order_type=OrderType.MARKET,
    limit_price=None,
    quantity=2,
):
    return PaperOrderIntent(
        intent_id=uuid4(),
        account_id=uuid4(),
        source=OrderSource.HUMAN,
        source_reference_id=SOURCE_REFERENCE_ID,
        symbol=symbol,
        asset_class=asset_class,
        side=OrderSide.BUY,
        quantity=quantity,
        order_type=order_type,
        limit_price=limit_price,
        time_in_force=TimeInForce.DAY,
        status=OrderIntentStatus.DRAFT,
        idempotency_key=f"riskguard-{symbol}-{uuid4()}",
        created_at=timestamp(),
    )


def timestamp():
    return datetime(2026, 6, 20, 13, 30, tzinfo=UTC)
