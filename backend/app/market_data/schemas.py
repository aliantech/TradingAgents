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


class ProviderSyncRunItem(BaseModel):
    id: str
    provider: str
    sync_type: str
    status: str
    started_at: datetime
    finished_at: datetime | None
    rows_written: int
    error_message: str | None = None


class ProviderSyncRunsResponse(BaseModel):
    runs: list[ProviderSyncRunItem]
