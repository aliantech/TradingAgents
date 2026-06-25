import re
from datetime import date
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.analysis.schemas import AnalysisProgressEvent, AnalysisRequest
from app.reports.quality import validate_research_report_quality
from app.reports.schemas import ResearchReport


class AdapterContract(BaseModel):
    model_config = ConfigDict(extra="forbid")


class TradingAgentsExecutionRequest(AdapterContract):
    analysis_id: UUID
    symbol: str
    asset_type: str
    analysis_date: date
    language: str
    llm_provider: str
    model: str
    depth: str
    analyst_set: str
    research_template: str
    runtime_config: dict[str, str]
    option_chain_context: str = ""


class TradingAgentsReportPayload(AdapterContract):
    summary: str = Field(min_length=1)
    market_background: str = Field(min_length=1)
    fundamental_analysis: str = Field(min_length=1)
    technical_analysis: str = Field(min_length=1)
    sentiment_analysis: str = Field(min_length=1)
    options_observation: str = Field(min_length=1)
    bull_case: str = Field(min_length=1)
    bear_case: str = Field(min_length=1)
    risk_factors: list[str]
    evidence_labels: list[str] = Field(default_factory=list)
    trade_plan: str = Field(min_length=1)
    position_sizing: str = Field(min_length=1)
    take_profit_stop_loss: str = Field(min_length=1)
    confidence: float = Field(ge=0, le=1)
    markdown: str | None = None


class TradingAgentsRunResult(AdapterContract):
    progress: list[AnalysisProgressEvent]
    report: TradingAgentsReportPayload


SENSITIVE_PATTERNS = (
    re.compile(r"api[_-]?key\s*=\s*[^,\s]+", re.IGNORECASE),
    re.compile(r"token\s*=\s*[^,\s]+", re.IGNORECASE),
    re.compile(r"password\s*=\s*[^,\s]+", re.IGNORECASE),
    re.compile(r"Bearer\s+[A-Za-z0-9._~+/=-]+", re.IGNORECASE),
    re.compile(r"sk-[A-Za-z0-9._-]+", re.IGNORECASE),
)


def build_tradingagents_request(
    analysis_id: UUID,
    request: AnalysisRequest,
    *,
    option_chain_context: str = "",
) -> TradingAgentsExecutionRequest:
    symbol = request.symbol.upper()
    runtime_config = {
        "symbol": symbol,
        "date": request.analysis_date.isoformat(),
        "llm_provider": request.llm_provider,
        "model": request.model,
        "depth": request.depth.value,
        "analyst_set": request.analyst_set,
        "research_template": request.research_template.value,
    }
    return TradingAgentsExecutionRequest(
        analysis_id=analysis_id,
        symbol=symbol,
        asset_type=request.asset_type.value,
        analysis_date=request.analysis_date,
        language=request.language.value,
        llm_provider=request.llm_provider,
        model=request.model,
        depth=request.depth.value,
        analyst_set=request.analyst_set,
        research_template=request.research_template.value,
        runtime_config=runtime_config,
        option_chain_context=option_chain_context,
    )


def tradingagents_result_to_report(
    *,
    execution_request: TradingAgentsExecutionRequest,
    result: TradingAgentsRunResult,
    report_id: UUID,
) -> ResearchReport:
    report = ResearchReport(
        report_id=report_id,
        analysis_id=execution_request.analysis_id,
        symbol=execution_request.symbol,
        language=execution_request.language,
        analyst_set=execution_request.analyst_set,
        research_template=execution_request.research_template,
        summary=result.report.summary,
        market_background=result.report.market_background,
        fundamental_analysis=result.report.fundamental_analysis,
        technical_analysis=result.report.technical_analysis,
        sentiment_analysis=result.report.sentiment_analysis,
        options_observation=result.report.options_observation,
        bull_case=result.report.bull_case,
        bear_case=result.report.bear_case,
        risk_factors=result.report.risk_factors,
        evidence_labels=result.report.evidence_labels,
        trade_plan=result.report.trade_plan,
        position_sizing=result.report.position_sizing,
        take_profit_stop_loss=result.report.take_profit_stop_loss,
        confidence=result.report.confidence,
        markdown=result.report.markdown,
    )
    validate_research_report_quality(report)
    return report


def map_tradingagents_error(error: Exception) -> AnalysisProgressEvent:
    return AnalysisProgressEvent(
        step="tradingagents",
        status="failed",
        message=f"TradingAgents research execution failed: {sanitize_error_message(str(error))}",
    )


def sanitize_error_message(message: str) -> str:
    sanitized = message
    for pattern in SENSITIVE_PATTERNS:
        sanitized = pattern.sub("[redacted]", sanitized)
    return sanitized
