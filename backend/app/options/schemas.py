from datetime import date, datetime

from pydantic import BaseModel, Field


class OptionSnapshot(BaseModel):
    option_symbol: str
    underlying_symbol: str
    timestamp: datetime
    bid: float | None = None
    ask: float | None = None
    last: float | None = None
    volume: int = Field(default=0, ge=0)
    open_interest: int | None = None
    implied_volatility: float | None = None
    delta: float | None = None
    gamma: float | None = None
    theta: float | None = None
    vega: float | None = None
    source: str


class OptionChainResponse(BaseModel):
    underlying_symbol: str
    expiry: str
    snapshots: list[OptionSnapshot]


class OptionContract(BaseModel):
    option_symbol: str
    underlying_symbol: str
    expiry: str
    strike: float
    option_type: str
    exercise_style: str | None = None
    expiration_type: str | None = None
    source: str


class OptionContractsResponse(BaseModel):
    underlying_symbol: str
    expiry: str | None = None
    contracts: list[OptionContract]


class OptionBar(BaseModel):
    option_symbol: str
    timeframe: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int = Field(ge=0)
    source: str


class OptionBarsResponse(BaseModel):
    option_symbol: str
    timeframe: str
    bars: list[OptionBar]


class OptionChainSyncRequest(BaseModel):
    underlying_symbol: str = Field(min_length=1, max_length=32)
    expiry: date
    provider: str = Field(default="polygon", min_length=1, max_length=64)
    limit: int = Field(default=250, ge=1, le=250)


class OptionChainSyncResponse(BaseModel):
    provider: str
    underlying_symbol: str
    expiry: str
    status: str
    rows_written: int
    error_message: str | None = None
