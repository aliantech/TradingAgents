from uuid import UUID

from pydantic import BaseModel, Field


class ResearchReport(BaseModel):
    analysis_id: UUID
    symbol: str
    language: str = "zh"
    summary: str
    market_background: str
    fundamental_analysis: str
    technical_analysis: str
    sentiment_analysis: str
    options_observation: str
    bull_case: str
    bear_case: str
    risk_factors: list[str]
    trade_plan: str
    position_sizing: str
    take_profit_stop_loss: str
    confidence: float = Field(ge=0.0, le=1.0)
