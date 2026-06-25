from datetime import datetime

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
