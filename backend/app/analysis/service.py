from uuid import uuid4

from app.analysis.repository import AnalysisRepository
from app.analysis.schemas import AnalysisProgressEvent, AnalysisRequest
from app.analysis.store import AnalysisRun, analysis_store


def _build_progress(symbol: str) -> list[AnalysisProgressEvent]:
    return [
        AnalysisProgressEvent(step="queued", status="completed", message=f"{symbol} 分析任务已进入队列。"),
        AnalysisProgressEvent(step="market_data", status="blocked", message="未生成报告：真实行情和研究 Agent 执行链尚未完成接入。"),
        AnalysisProgressEvent(step="report", status="failed", message="未生成研究报告；系统不再写入样例或 mock 报告。"),
    ]


def start_analysis(request: AnalysisRequest, repository: AnalysisRepository | None = None) -> AnalysisRun:
    analysis_id = uuid4()
    normalized_request = request.model_copy(update={"symbol": request.symbol.upper()})
    run = AnalysisRun(
        analysis_id=analysis_id,
        request=normalized_request,
        status="failed",
        progress=_build_progress(normalized_request.symbol),
    )
    if repository is not None:
        repository.save_run(run)
    return analysis_store.save(run)
