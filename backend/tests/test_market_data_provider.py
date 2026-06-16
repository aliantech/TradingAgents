from datetime import date

from app.market_data.provider import MarketDataProvider


class FakeProvider(MarketDataProvider):
    def fetch_daily_bars(self, symbol: str, start: date, end: date):
        return []


def test_provider_interface_supports_daily_bars():
    provider = FakeProvider()
    bars = provider.fetch_daily_bars("SPY", date(2026, 6, 1), date(2026, 6, 17))

    assert bars == []
