from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.analysis.repository import AnalysisRepository
from app.analysis.store import analysis_store
from app.db.session import get_db_session
from app.reports.schemas import ReportListItem, ResearchReport

router = APIRouter(prefix="/api/reports", tags=["reports"])


def get_analysis_repository(session: Session = Depends(get_db_session)) -> AnalysisRepository:
    return AnalysisRepository(session)


@router.get("", response_model=list[ReportListItem])
def list_reports(repository: AnalysisRepository = Depends(get_analysis_repository)) -> list[ReportListItem]:
    persisted_reports = repository.list_reports()
    if persisted_reports:
        return persisted_reports

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
def get_report(
    report_id: UUID,
    repository: AnalysisRepository = Depends(get_analysis_repository),
) -> ResearchReport:
    persisted_report = repository.get_report(report_id)
    if persisted_report is not None:
        return persisted_report

    for run in analysis_store.list_runs():
        if run.report and run.report.report_id == report_id:
            return run.report
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="report not found")
