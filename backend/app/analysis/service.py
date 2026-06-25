from uuid import uuid4

from app.analysis.repository import AnalysisRepository
from app.analysis.schemas import AnalysisProgressEvent, AnalysisRequest
from app.analysis.option_chain_context import build_option_chain_context
from app.analysis.store import AnalysisRun, analysis_store
from app.analysis.tradingagents_adapter import (
    build_tradingagents_request,
    map_tradingagents_error,
    tradingagents_result_to_report,
)
from app.analysis.tradingagents_runner import run_configured_research
from app.core.config import settings
from app.reports.quality import ReportQualityError
from app.settings.runtime import resolve_runtime_settings


def _build_progress(symbol: str) -> list[AnalysisProgressEvent]:
    return [
        AnalysisProgressEvent(step="queued", status="completed", message=f"{symbol} 分析任务已进入队列。"),
        AnalysisProgressEvent(step="market_data", status="blocked", message="未生成报告：真实行情和研究 Agent 执行链尚未完成接入。"),
        AnalysisProgressEvent(step="report", status="failed", message="未生成研究报告；系统不再写入样例或 mock 报告。"),
    ]


def _build_report_quality_failure(error: ReportQualityError) -> AnalysisProgressEvent:
    return AnalysisProgressEvent(step="report_quality", status="failed", message=str(error))


def _append_report_quality_failure(
    progress: list[AnalysisProgressEvent],
    error: ReportQualityError,
) -> list[AnalysisProgressEvent]:
    return progress + [_build_report_quality_failure(error)]


def start_analysis(request: AnalysisRequest, repository: AnalysisRepository | None = None) -> AnalysisRun:
    analysis_id = uuid4()
    normalized_request = request.model_copy(update={"symbol": request.symbol.upper()})
    option_chain_context = (
        build_option_chain_context(
            repository.session,
            symbol=normalized_request.symbol,
            analysis_date=normalized_request.analysis_date,
        )
        if repository is not None
        else ""
    )
    execution_request = build_tradingagents_request(
        analysis_id,
        normalized_request,
        option_chain_context=option_chain_context,
    )
    runtime_settings = resolve_runtime_settings(repository.session) if repository is not None else settings
    try:
        result = run_configured_research(execution_request, runtime_settings)
        report = tradingagents_result_to_report(
            execution_request=execution_request,
            result=result,
            report_id=uuid4(),
        )
        run = AnalysisRun(
            analysis_id=analysis_id,
            request=normalized_request,
            status="completed",
            progress=result.progress,
            report=report,
        )
    except ReportQualityError as error:
        run = AnalysisRun(
            analysis_id=analysis_id,
            request=normalized_request,
            status="failed",
            progress=_append_report_quality_failure(result.progress, error),
        )
    except Exception as error:
        run = AnalysisRun(
            analysis_id=analysis_id,
            request=normalized_request,
            status="failed",
            progress=_build_progress(normalized_request.symbol) + [map_tradingagents_error(error)],
        )
    if repository is not None:
        repository.save_run(run)
    return analysis_store.save(run)
