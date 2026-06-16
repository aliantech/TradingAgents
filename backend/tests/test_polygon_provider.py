from datetime import date

import pytest

from app.market_data.polygon_provider import PolygonMarketDataProvider, ProviderRateLimitError
from app.market_data.provider_registry import get_market_data_provider


class FakePolygonTransport:
    def __init__(self, responses: list[dict]) -> None:
        self.responses = responses
        self.calls: list[str] = []

    def get_json(self, url: str) -> dict:
        self.calls.append(url)
        response = self.responses.pop(0)
        if response.get("status_code") == 429:
            raise ProviderRateLimitError("rate limited")
        return response


def test_polygon_provider_converts_aggregate_payload_to_daily_bars():
    transport = FakePolygonTransport(
        [
            {
                "ticker": "SPY",
                "results": [
                    {"t": 1781654400000, "o": 550.0, "h": 553.0, "l": 549.5, "c": 552.2, "v": 90000000}
                ],
            }
        ]
    )
    provider = PolygonMarketDataProvider(api_key="test-key", transport=transport)

    bars = provider.fetch_daily_bars("spy", date(2026, 6, 17), date(2026, 6, 17))

    assert len(bars) == 1
    assert bars[0].symbol == "SPY"
    assert bars[0].timeframe == "1d"
    assert bars[0].open == 550.0
    assert bars[0].close == 552.2
    assert bars[0].volume == 90000000
    assert bars[0].source == "polygon"
    assert "/v2/aggs/ticker/SPY/range/1/day/2026-06-17/2026-06-17" in transport.calls[0]


def test_polygon_provider_retries_rate_limits_before_succeeding():
    sleeps: list[float] = []
    transport = FakePolygonTransport(
        [
            {"status_code": 429},
            {"ticker": "SPY", "results": []},
        ]
    )
    provider = PolygonMarketDataProvider(
        api_key="test-key",
        transport=transport,
        max_retries=1,
        retry_backoff_seconds=0.25,
        sleep=sleeps.append,
    )

    bars = provider.fetch_daily_bars("SPY", date(2026, 6, 17), date(2026, 6, 17))

    assert bars == []
    assert len(transport.calls) == 2
    assert sleeps == [0.25]


def test_polygon_provider_registry_requires_api_key():
    with pytest.raises(ValueError, match="AQUANTLENS_POLYGON_API_KEY"):
        get_market_data_provider("polygon", polygon_api_key="")
