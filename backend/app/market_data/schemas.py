from datetime import date, datetime

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


class DailyBarSyncRequest(BaseModel):
    symbol: str = Field(min_length=1, max_length=32)
    start: date
    end: date
    timeframe: str = Field(default="1d", pattern="^(1m|5m|1d)$")
    provider: str | None = None


class DailyBarSyncResponse(BaseModel):
    status: str
    rows_written: int
    error_message: str | None = None
