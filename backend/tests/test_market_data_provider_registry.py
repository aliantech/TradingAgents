from datetime import date

import pytest

from app.market_data.provider_registry import get_market_data_provider


def test_provider_registry_returns_sample_provider():
    provider = get_market_data_provider("sample")

    bars = provider.fetch_daily_bars("SPY", date(2026, 6, 16), date(2026, 6, 17))

    assert len(bars) == 2
    assert bars[0].symbol == "SPY"
    assert bars[0].timeframe == "1d"
    assert bars[0].source == "sample"


def test_provider_registry_rejects_unknown_provider():
    with pytest.raises(ValueError, match="Unsupported market data provider"):
        get_market_data_provider("missing")
