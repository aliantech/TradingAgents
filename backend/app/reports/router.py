from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from app.analysis.store import analysis_store
from app.reports.schemas import ReportListItem, ResearchReport

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.get("", response_model=list[ReportListItem])
def list_reports() -> list[ReportListItem]:
    reports: list[ReportListItem] = []
    for run in analysis_store.list_runs():
        if run.report is None or run.report.report_id is None:
            continue
        reports.append(
            ReportListItem(
                report_id=run.report.report_id,
                analysis_id=run.analysis_id,
                symbol=run.report.symbol,
                language=run.report.language,
                summary=run.report.summary,
                confidence=run.report.confidence,
            )
        )
    return reports


@router.get("/{report_id}", response_model=ResearchReport)
def get_report(report_id: UUID) -> ResearchReport:
    for run in analysis_store.list_runs():
        if run.report and run.report.report_id == report_id:
            return run.report
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="report not found")
