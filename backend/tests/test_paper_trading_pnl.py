from datetime import datetime, timedelta
from uuid import uuid4

from app.paper_trading.contracts import (
    AssetClass,
    OrderSide,
    PaperAccount,
    PaperAccountStatus,
    PaperFill,
    PaperPosition,
)
from app.paper_trading.pnl import (
    ReferencePrice,
    calculate_paper_pnl_snapshot,
    calculate_realized_pnl,
)


def test_paper_pnl_snapshot_prices_equity_and_option_positions():
    account = paper_account(current_cash=10_000)
    spy_position = paper_position(account.account_id, symbol="SPY", asset_class=AssetClass.ETF, quantity=2, average_price=500)
    spx_option = paper_position(
        account.account_id,
        symbol="SPXW-20260620-5500-C",
        asset_class=AssetClass.INDEX_OPTION,
        quantity=1,
        average_price=20,
    )

    snapshot = calculate_paper_pnl_snapshot(
        account=account,
        positions=[spy_position, spx_option],
        reference_prices=[
            reference_price("SPY", AssetClass.ETF, 510),
            reference_price("SPXW-20260620-5500-C", AssetClass.INDEX_OPTION, 25),
        ],
        as_of=timestamp(),
        realized_pnl=125,
    )

    assert snapshot.price_state == "complete"
    assert snapshot.total_market_value == 3_520
    assert snapshot.total_unrealized_pnl == 520
    assert snapshot.total_realized_pnl == 125
    assert snapshot.account_equity == 13_520
    assert snapshot.positions[0].market_value == 1_020
    assert snapshot.positions[0].unrealized_pnl == 20
    assert snapshot.positions[1].multiplier == 100
    assert snapshot.positions[1].market_value == 2_500
    assert snapshot.positions[1].unrealized_pnl == 500


def test_paper_pnl_snapshot_marks_missing_and_stale_prices_without_fetching_quotes():
    account = paper_account(current_cash=10_000)
    spy_position = paper_position(account.account_id, symbol="SPY", asset_class=AssetClass.ETF, quantity=2, average_price=500)
    qqq_position = paper_position(account.account_id, symbol="QQQ", asset_class=AssetClass.ETF, quantity=1, average_price=400)

    snapshot = calculate_paper_pnl_snapshot(
        account=account,
        positions=[spy_position, qqq_position],
        reference_prices=[
            reference_price("SPY", AssetClass.ETF, 510, priced_at=timestamp() - timedelta(minutes=30)),
        ],
        as_of=timestamp(),
        max_price_age_seconds=60,
    )

    assert snapshot.price_state == "partial"
    assert snapshot.total_market_value == 0
    assert snapshot.account_equity == 10_000
    assert [row.price_state for row in snapshot.positions] == ["stale", "missing"]
    assert snapshot.positions[0].market_value is None
    assert snapshot.positions[1].reference_price is None


def test_paper_pnl_snapshot_supports_short_like_position_unrealized_pnl():
    account = paper_account(current_cash=10_000)
    short_position = paper_position(account.account_id, symbol="SPY", asset_class=AssetClass.ETF, quantity=-2, average_price=500)

    snapshot = calculate_paper_pnl_snapshot(
        account=account,
        positions=[short_position],
        reference_prices=[reference_price("SPY", AssetClass.ETF, 490)],
        as_of=timestamp(),
    )

    assert snapshot.positions[0].market_value == -980
    assert snapshot.positions[0].unrealized_pnl == 20
    assert snapshot.account_equity == 9_020


def test_paper_realized_pnl_uses_local_paper_fills_only():
    account_id = uuid4()
    fills = [
        paper_fill(account_id, OrderSide.BUY, quantity=3, fill_price=450, seconds=0),
        paper_fill(account_id, OrderSide.SELL, quantity=1, fill_price=500, seconds=1),
    ]

    assert calculate_realized_pnl(fills) == 50


def paper_account(*, current_cash=100_000):
    return PaperAccount(
        account_id=uuid4(),
        name="PnL paper account",
        base_currency="USD",
        starting_cash=100_000,
        current_cash=current_cash,
        status=PaperAccountStatus.ACTIVE,
        created_at=timestamp(),
    )


def paper_position(account_id, *, symbol, asset_class, quantity, average_price):
    return PaperPosition(
        position_id=uuid4(),
        account_id=account_id,
        symbol=symbol,
        asset_class=asset_class,
        quantity=quantity,
        average_price=average_price,
        updated_at=timestamp(),
    )


def reference_price(symbol, asset_class, price, *, priced_at=None):
    return ReferencePrice(
        symbol=symbol,
        asset_class=asset_class,
        price=price,
        priced_at=priced_at or timestamp(),
    )


def paper_fill(account_id, side, *, quantity, fill_price, seconds):
    return PaperFill(
        fill_id=uuid4(),
        intent_id=uuid4(),
        account_id=account_id,
        symbol="SPY",
        asset_class=AssetClass.ETF,
        side=side,
        quantity=quantity,
        fill_price=fill_price,
        filled_at=timestamp() + timedelta(seconds=seconds),
    )


def timestamp():
    return datetime(2026, 6, 20, 13, 30)
