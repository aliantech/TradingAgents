from datetime import date, datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, Field


class AssetType(StrEnum):
    equity = "equity"
    etf = "etf"
    index = "index"
    option = "option"


class ReportLanguage(StrEnum):
    zh = "zh"
    en = "en"


class AnalysisDepth(StrEnum):
    quick = "quick"
    standard = "standard"
    deep = "deep"


class AnalysisRequest(BaseModel):
    symbol: str = Field(min_length=1, max_length=64)
    asset_type: AssetType
    analysis_date: date
    language: ReportLanguage = ReportLanguage.zh
    llm_provider: str = Field(min_length=1, max_length=64)
    model: str = Field(min_length=1, max_length=128)
    depth: AnalysisDepth = AnalysisDepth.standard
    analyst_set: str = Field(default="macro-options", min_length=1, max_length=64)


class AnalysisQueuedResponse(BaseModel):
    analysis_id: UUID
    symbol: str
    status: str
    language: ReportLanguage


class AnalysisProgressEvent(BaseModel):
    step: str
    status: str
    message: str


class AnalysisStatusResponse(BaseModel):
    analysis_id: UUID
    symbol: str
    asset_type: AssetType
    status: str
    language: ReportLanguage
    progress: list[AnalysisProgressEvent]
    report_id: UUID | None = None


class AnalysisRunListItem(BaseModel):
    analysis_id: UUID
    symbol: str
    asset_type: AssetType
    status: str
    language: ReportLanguage
    analysis_date: date
    llm_provider: str
    model: str
    depth: AnalysisDepth
    analyst_set: str
    created_at: datetime
    updated_at: datetime
    report_id: UUID | None = None


class AnalysisRunsResponse(BaseModel):
    runs: list[AnalysisRunListItem]
