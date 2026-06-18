import pytest

from app.market_data.polygon_provider import PolygonMarketDataProvider
from app.market_data.provider_registry import get_market_data_provider


def test_provider_registry_returns_polygon_provider():
    provider = get_market_data_provider("polygon", polygon_api_key="test-key")

    assert isinstance(provider, PolygonMarketDataProvider)


def test_provider_registry_rejects_sample_provider():
    with pytest.raises(ValueError, match="Unsupported market data provider"):
        get_market_data_provider("sample")


def test_provider_registry_rejects_unknown_provider():
    with pytest.raises(ValueError, match="Unsupported market data provider"):
        get_market_data_provider("missing")
