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
