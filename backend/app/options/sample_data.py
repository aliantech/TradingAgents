from datetime import UTC, date, datetime

from app.options.repository import OptionContractRecord, OptionRepository, OptionSnapshotRecord


def seed_sample_option_chain(
    repository: OptionRepository,
    *,
    underlying_symbol: str,
    expiry: date,
) -> None:
    underlying = underlying_symbol.upper()
    timestamp = datetime(2026, 6, 17, 13, 30, tzinfo=UTC)
    base_strikes = {
        "SPX": [5900.0, 5950.0, 6000.0, 6050.0, 6100.0],
        "SPY": [540.0, 545.0, 550.0, 555.0, 560.0],
        "QQQ": [470.0, 475.0, 480.0, 485.0, 490.0],
    }
    strikes = base_strikes.get(underlying, base_strikes["SPX"])
    for index, strike in enumerate(strikes):
        option_symbol = _sample_option_symbol(underlying=underlying, expiry=expiry, strike=strike)
        repository.upsert_contract(
            OptionContractRecord(
                option_symbol=option_symbol,
                underlying_symbol=underlying,
                expiry=expiry,
                strike=strike,
                option_type="call",
                exercise_style="european" if underlying.startswith("SPX") else "american",
                expiration_type="weekly",
                source="sample",
            )
        )
        repository.upsert_snapshot(
            OptionSnapshotRecord(
                option_symbol=option_symbol,
                underlying_symbol=underlying,
                timestamp=timestamp,
                bid=round(8.5 + index * 1.2, 2),
                ask=round(8.9 + index * 1.2, 2),
                last=round(8.7 + index * 1.2, 2),
                volume=1200 - index * 90,
                open_interest=8000 + index * 350,
                implied_volatility=round(0.18 + index * 0.006, 4),
                delta=round(0.35 + index * 0.06, 4),
                gamma=round(0.018 + index * 0.001, 4),
                theta=round(-0.14 - index * 0.01, 4),
                vega=round(0.31 + index * 0.02, 4),
                source="sample",
            )
        )


def _sample_option_symbol(*, underlying: str, expiry: date, strike: float) -> str:
    expiry_code = expiry.strftime("%y%m%d")
    strike_code = int(strike * 1000)
    return f"{underlying}W{expiry_code}C{strike_code:08d}"
