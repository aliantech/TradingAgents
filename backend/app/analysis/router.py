from uuid import uuid4

from fastapi import APIRouter, status

from app.analysis.schemas import AnalysisQueuedResponse, AnalysisRequest

router = APIRouter(prefix="/api/analysis", tags=["analysis"])


@router.post("", response_model=AnalysisQueuedResponse, status_code=status.HTTP_202_ACCEPTED)
def start_analysis(request: AnalysisRequest) -> AnalysisQueuedResponse:
    return AnalysisQueuedResponse(
        analysis_id=uuid4(),
        symbol=request.symbol.upper(),
        status="queued",
        language=request.language,
    )
