from abc import ABC, abstractmethod
from datetime import date

from app.market_data.schemas import MarketBar


class MarketDataProvider(ABC):
    @abstractmethod
    def fetch_daily_bars(self, symbol: str, start: date, end: date) -> list[MarketBar]:
        raise NotImplementedError
