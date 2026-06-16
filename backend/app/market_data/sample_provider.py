from datetime import UTC, date, datetime, time, timedelta

from app.market_data.provider import MarketDataProvider
from app.market_data.schemas import MarketBar


class SampleMarketDataProvider(MarketDataProvider):
    def fetch_daily_bars(self, symbol: str, start: date, end: date) -> list[MarketBar]:
        normalized_symbol = symbol.upper()
        bars: list[MarketBar] = []
        current = start
        index = 0
        while current <= end:
            base_price = 540.0 + index * 1.25
            bars.append(
                MarketBar(
                    symbol=normalized_symbol,
                    timeframe="1d",
                    timestamp=datetime.combine(current, time(20, 0), tzinfo=UTC),
                    open=base_price,
                    high=base_price + 3.0,
                    low=base_price - 2.0,
                    close=base_price + 1.4,
                    volume=80_000_000 + index * 1_000_000,
                    source="sample",
                )
            )
            current += timedelta(days=1)
            index += 1
        return bars
