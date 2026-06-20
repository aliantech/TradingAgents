from datetime import UTC, datetime, timedelta
from typing import Literal

from pydantic import Field

from app.paper_trading.contracts import (
    AssetClass,
    OrderSide,
    PaperAccount,
    PaperFill,
    PaperPosition,
    StrictContract,
)


OPTION_ASSET_CLASSES = {AssetClass.INDEX_OPTION, AssetClass.EQUITY_OPTION}


class ReferencePrice(StrictContract):
    symbol: str = Field(min_length=1, max_length=64)
    asset_class: AssetClass
    price: float = Field(gt=0, allow_inf_nan=False)
    priced_at: datetime


class PaperPositionPnl(StrictContract):
    position_id: str
    account_id: str
    symbol: str
    asset_class: str
    quantity: float
    average_price: float
    multiplier: int
    price_state: Literal["fresh", "stale", "missing"]
    reference_price: float | None = None
    reference_priced_at: datetime | None = None
    market_value: float | None = None
    cost_basis: float | None = None
    unrealized_pnl: float | None = None


class PaperPnlSnapshot(StrictContract):
    account_id: str
    base_currency: str
    current_cash: float
    as_of: datetime
    price_state: Literal["complete", "partial"]
    total_market_value: float
    total_unrealized_pnl: float
    total_realized_pnl: float
    account_equity: float
    positions: list[PaperPositionPnl]


def calculate_paper_pnl_snapshot(
    *,
    account: PaperAccount,
    positions: list[PaperPosition],
    reference_prices: list[ReferencePrice],
    as_of: datetime,
    max_price_age_seconds: int = 900,
    realized_pnl: float = 0,
) -> PaperPnlSnapshot:
    reference_by_key = {(price.symbol.upper(), price.asset_class): price for price in reference_prices}
    position_rows = [
        calculate_position_pnl(
            position,
            reference_by_key.get((position.symbol.upper(), position.asset_class)),
            as_of=as_of,
            max_price_age_seconds=max_price_age_seconds,
        )
        for position in positions
    ]
    total_market_value = money(sum(row.market_value or 0 for row in position_rows))
    total_unrealized_pnl = money(sum(row.unrealized_pnl or 0 for row in position_rows))
    return PaperPnlSnapshot(
        account_id=str(account.account_id),
        base_currency=account.base_currency,
        current_cash=account.current_cash,
        as_of=as_of,
        price_state="complete" if all(row.price_state == "fresh" for row in position_rows) else "partial",
        total_market_value=total_market_value,
        total_unrealized_pnl=total_unrealized_pnl,
        total_realized_pnl=money(realized_pnl),
        account_equity=money(account.current_cash + total_market_value),
        positions=position_rows,
    )


def calculate_position_pnl(
    position: PaperPosition,
    reference_price: ReferencePrice | None,
    *,
    as_of: datetime,
    max_price_age_seconds: int,
) -> PaperPositionPnl:
    multiplier = multiplier_for(position.asset_class)
    base = {
        "position_id": str(position.position_id),
        "account_id": str(position.account_id),
        "symbol": position.symbol,
        "asset_class": position.asset_class.value,
        "quantity": position.quantity,
        "average_price": position.average_price,
        "multiplier": multiplier,
    }
    if reference_price is None:
        return PaperPositionPnl(**base, price_state="missing")
    if is_stale(reference_price.priced_at, as_of=as_of, max_price_age_seconds=max_price_age_seconds):
        return PaperPositionPnl(
            **base,
            price_state="stale",
            reference_price=reference_price.price,
            reference_priced_at=reference_price.priced_at,
        )

    market_value = money(position.quantity * reference_price.price * multiplier)
    cost_basis = money(position.quantity * position.average_price * multiplier)
    return PaperPositionPnl(
        **base,
        price_state="fresh",
        reference_price=reference_price.price,
        reference_priced_at=reference_price.priced_at,
        market_value=market_value,
        cost_basis=cost_basis,
        unrealized_pnl=money(market_value - cost_basis),
    )


def calculate_realized_pnl(fills: list[PaperFill]) -> float:
    quantity_by_key: dict[tuple[str, AssetClass], float] = {}
    average_by_key: dict[tuple[str, AssetClass], float] = {}
    realized = 0.0

    for fill in sorted(fills, key=lambda row: (row.filled_at, row.fill_id)):
        key = (fill.symbol.upper(), fill.asset_class)
        multiplier = multiplier_for(fill.asset_class)
        current_quantity = quantity_by_key.get(key, 0)
        current_average = average_by_key.get(key, 0)
        if fill.side == OrderSide.BUY:
            next_quantity = current_quantity + fill.quantity
            if next_quantity:
                average_by_key[key] = (
                    (current_quantity * current_average) + (fill.quantity * fill.fill_price)
                ) / next_quantity
            quantity_by_key[key] = next_quantity
            continue

        closed_quantity = min(fill.quantity, max(current_quantity, 0))
        realized += (fill.fill_price - current_average) * closed_quantity * multiplier
        quantity_by_key[key] = current_quantity - fill.quantity
        if quantity_by_key[key] <= 0:
            average_by_key[key] = 0

    return money(realized)


def multiplier_for(asset_class: AssetClass) -> int:
    return 100 if asset_class in OPTION_ASSET_CLASSES else 1


def is_stale(priced_at: datetime, *, as_of: datetime, max_price_age_seconds: int) -> bool:
    return comparable_utc(priced_at) < comparable_utc(as_of) - timedelta(seconds=max_price_age_seconds)


def comparable_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value
    return value.astimezone(UTC).replace(tzinfo=None)


def money(value: float) -> float:
    return round(value, 4)
