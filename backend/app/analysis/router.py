import json
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse

from app.analysis.schemas import AnalysisQueuedResponse, AnalysisRequest, AnalysisStatusResponse
from app.analysis.service import start_analysis as start_analysis_job
from app.analysis.store import analysis_store

router = APIRouter(prefix="/api/analysis", tags=["analysis"])


@router.post("", response_model=AnalysisQueuedResponse, status_code=status.HTTP_202_ACCEPTED)
def start_analysis(request: AnalysisRequest) -> AnalysisQueuedResponse:
    run = start_analysis_job(request)
    return AnalysisQueuedResponse(
        analysis_id=run.analysis_id,
        symbol=run.request.symbol,
        status="queued",
        language=run.request.language,
    )


@router.get("/{analysis_id}", response_model=AnalysisStatusResponse)
def get_analysis_status(analysis_id: UUID) -> AnalysisStatusResponse:
    run = analysis_store.get(analysis_id)
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
def stream_analysis_events(analysis_id: UUID) -> StreamingResponse:
    run = analysis_store.get(analysis_id)
    if run is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="analysis not found")

    def event_stream():
        for event in run.progress:
            yield f"data: {json.dumps(event.model_dump(), ensure_ascii=False)}\n\n"
        yield 'event: done\ndata: {"status":"completed"}\n\n'

    return StreamingResponse(event_stream(), media_type="text/event-stream")
