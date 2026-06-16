from abc import ABC, abstractmethod
from datetime import date

from app.market_data.schemas import MarketBar


class MarketDataProvider(ABC):
    def fetch_bars(self, symbol: str, timeframe: str, start: date, end: date) -> list[MarketBar]:
        if timeframe == "1d":
            return self.fetch_daily_bars(symbol, start, end)
        raise NotImplementedError(f"{self.__class__.__name__} does not support {timeframe} bars.")

    @abstractmethod
    def fetch_daily_bars(self, symbol: str, start: date, end: date) -> list[MarketBar]:
        raise NotImplementedError
