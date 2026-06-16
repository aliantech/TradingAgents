from datetime import datetime

from pydantic import BaseModel, Field


class MarketBar(BaseModel):
    symbol: str
    timeframe: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int = Field(ge=0)
    source: str


class MarketBarsResponse(BaseModel):
    symbol: str
    timeframe: str
    bars: list[MarketBar]
