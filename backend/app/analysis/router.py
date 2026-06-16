import json
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.analysis.repository import AnalysisRepository
from app.analysis.schemas import AnalysisQueuedResponse, AnalysisRequest, AnalysisStatusResponse
from app.analysis.service import start_analysis as start_analysis_job
from app.analysis.store import analysis_store
from app.db.session import get_db_session

router = APIRouter(prefix="/api/analysis", tags=["analysis"])


def get_analysis_repository(session: Session = Depends(get_db_session)) -> AnalysisRepository:
    return AnalysisRepository(session)


@router.post("", response_model=AnalysisQueuedResponse, status_code=status.HTTP_202_ACCEPTED)
def start_analysis(
    request: AnalysisRequest,
    repository: AnalysisRepository = Depends(get_analysis_repository),
) -> AnalysisQueuedResponse:
    run = start_analysis_job(request, repository=repository)
    return AnalysisQueuedResponse(
        analysis_id=run.analysis_id,
        symbol=run.request.symbol,
        status="queued",
        language=run.request.language,
    )


@router.get("/{analysis_id}", response_model=AnalysisStatusResponse)
def get_analysis_status(
    analysis_id: UUID,
    repository: AnalysisRepository = Depends(get_analysis_repository),
) -> AnalysisStatusResponse:
    run = repository.get_run(analysis_id) or analysis_store.get(analysis_id)
    if run is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="analysis not found")

    return AnalysisStatusResponse(
        analysis_id=run.analysis_id,
        symbol=run.request.symbol,
        asset_type=run.request.asset_type,
        status=run.status,
        language=run.request.language,
        progress=run.progress,
        report_id=run.report.report_id if run.report else None,
    )


@router.get("/{analysis_id}/events")
def stream_analysis_events(
    analysis_id: UUID,
    repository: AnalysisRepository = Depends(get_analysis_repository),
) -> StreamingResponse:
    run = repository.get_run(analysis_id) or analysis_store.get(analysis_id)
    if run is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="analysis not found")

    def event_stream():
        for event in run.progress:
            yield f"data: {json.dumps(event.model_dump(), ensure_ascii=False)}\n\n"
        yield 'event: done\ndata: {"status":"completed"}\n\n'

    return StreamingResponse(event_stream(), media_type="text/event-stream")
