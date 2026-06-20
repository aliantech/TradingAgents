from uuid import UUID

from pydantic import BaseModel, Field


class ResearchReport(BaseModel):
    analysis_id: UUID
    report_id: UUID | None = None
    symbol: str
    language: str = "zh"
    analyst_set: str = "macro-options"
    research_template: str = "general"
    summary: str
    market_background: str
    fundamental_analysis: str
    technical_analysis: str
    sentiment_analysis: str
    options_observation: str
    bull_case: str
    bear_case: str
    risk_factors: list[str]
    evidence_labels: list[str] = Field(default_factory=list)
    trade_plan: str
    position_sizing: str
    take_profit_stop_loss: str
    confidence: float = Field(ge=0.0, le=1.0)
    markdown: str | None = None


class ReportListItem(BaseModel):
    report_id: UUID
    analysis_id: UUID
    symbol: str
    language: str
    analyst_set: str = "macro-options"
    research_template: str = "general"
    summary: str
    confidence: float


class ReportComparisonSection(BaseModel):
    current: str
    previous: str
    changed: bool


class ReportRiskFactorChanges(BaseModel):
    added: list[str]
    removed: list[str]


class ReportComparison(BaseModel):
    symbol: str
    current: ReportListItem
    previous: ReportListItem
    confidence_delta: float
    risk_factor_changes: ReportRiskFactorChanges
    section_changes: dict[str, ReportComparisonSection]


class ReportReviewCreate(BaseModel):
    reviewer: str = Field(default="operator", min_length=1, max_length=80)
    evidence_clarity: int = Field(ge=1, le=5)
    consistency: int = Field(ge=1, le=5)
    risk_coverage: int = Field(ge=1, le=5)
    options_relevance: int = Field(ge=1, le=5)
    chinese_readability: int = Field(ge=1, le=5)
    research_only_safety: int = Field(ge=1, le=5)
    notes: str = Field(default="", max_length=2000)


class ReportReview(ReportReviewCreate):
    review_id: UUID
    report_id: UUID
    created_at: str
