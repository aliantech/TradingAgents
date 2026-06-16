import pytest

from app.market_data.symbols import map_provider_symbol


@pytest.mark.parametrize(
    ("symbol", "provider", "expected"),
    [
        ("spy", "polygon", "SPY"),
        ("qqq", "polygon", "QQQ"),
        ("spx", "polygon", "I:SPX"),
        ("aapl", "polygon", "AAPL"),
        ("spy", "sample", "SPY"),
    ],
)
def test_map_provider_symbol(symbol: str, provider: str, expected: str):
    assert map_provider_symbol(symbol, provider) == expected
