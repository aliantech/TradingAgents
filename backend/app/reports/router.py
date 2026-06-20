from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.analysis.repository import AnalysisRepository, build_report_comparison, is_legacy_mock_report
from app.analysis.store import analysis_store
from app.db.session import get_db_session
from app.reports.schemas import ReportComparison, ReportListItem, ReportReview, ReportReviewCreate, ResearchReport

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
        if is_legacy_mock_report(run.report.model_dump(mode="json")):
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
            if is_legacy_mock_report(run.report.model_dump(mode="json")):
                break
            return run.report
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="report not found")


@router.post("/{report_id}/reviews", response_model=ReportReview, status_code=status.HTTP_201_CREATED)
def create_report_review(
    report_id: UUID,
    review: ReportReviewCreate,
    repository: AnalysisRepository = Depends(get_analysis_repository),
) -> ReportReview:
    created = repository.create_report_review(report_id, review)
    if created is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="report not found")
    return created


@router.get("/{report_id}/reviews", response_model=list[ReportReview])
def list_report_reviews(
    report_id: UUID,
    repository: AnalysisRepository = Depends(get_analysis_repository),
) -> list[ReportReview]:
    reviews = repository.list_report_reviews(report_id)
    if reviews is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="report not found")
    return reviews


@router.get("/{report_id}/comparison", response_model=ReportComparison)
def get_report_comparison(
    report_id: UUID,
    repository: AnalysisRepository = Depends(get_analysis_repository),
) -> ReportComparison:
    persisted_comparison = repository.get_report_comparison(report_id)
    if persisted_comparison is not None:
        return persisted_comparison
    if repository.get_report(report_id) is not None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="previous report not found")

    current = None
    previous = None
    for run in analysis_store.list_runs():
        if run.report and run.report.report_id == report_id:
            if is_legacy_mock_report(run.report.model_dump(mode="json")):
                break
            current = run
            break
    if current is None or current.report is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="report not found")

    for run in analysis_store.list_runs():
        if (
            run.report
            and run.report.report_id != report_id
            and run.report.symbol == current.report.symbol
            and run.request.analysis_date < current.request.analysis_date
            and not is_legacy_mock_report(run.report.model_dump(mode="json"))
        ):
            if previous is None or run.request.analysis_date > previous.request.analysis_date:
                previous = run
    if previous is None or previous.report is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="previous report not found")
    return build_report_comparison(current=current.report, previous=previous.report)
