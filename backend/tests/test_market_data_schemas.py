from datetime import datetime, timezone

from app.market_data.schemas import MarketBar
from app.options.schemas import OptionSnapshot


def test_market_bar_contract():
    bar = MarketBar(
        symbol="SPY",
        timeframe="1m",
        timestamp=datetime(2026, 6, 17, 13, 30, tzinfo=timezone.utc),
        open=550.0,
        high=551.0,
        low=549.5,
        close=550.5,
        volume=1000000,
        source="provider",
    )

    assert bar.symbol == "SPY"
    assert bar.timeframe == "1m"


def test_option_snapshot_contract():
    snapshot = OptionSnapshot(
        option_symbol="SPXW260617C06000000",
        underlying_symbol="SPX",
        timestamp=datetime(2026, 6, 17, 13, 30, tzinfo=timezone.utc),
        bid=10.1,
        ask=10.4,
        last=10.2,
        volume=1200,
        open_interest=8000,
        implied_volatility=0.18,
        delta=0.48,
        gamma=0.02,
        theta=-0.15,
        vega=0.34,
        source="provider",
    )

    assert snapshot.underlying_symbol == "SPX"
    assert snapshot.delta == 0.48
