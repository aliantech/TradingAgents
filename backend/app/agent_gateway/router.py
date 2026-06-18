from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agent_gateway.auth import (
    ensure_instrument_allowed,
    get_current_agent_token,
    list_matches,
    parse_csv,
    record_agent_audit,
    require_scope,
)
from app.analysis.repository import AnalysisRepository
from app.analysis.schemas import AnalysisProgressEvent, AnalysisRequest
from app.analysis.service import start_analysis as start_analysis_job
from app.db.models import AgentJobModel, AgentTokenModel
from app.db.session import get_db_session
from app.reports.schemas import ReportListItem, ResearchReport

router = APIRouter(prefix="/api/agent/v1", tags=["agent-gateway"])
RESEARCH_ANALYSIS_JOB_TYPE = "research_analysis"


class AgentJobResult(BaseModel):
    analysis_id: UUID
    report_id: UUID | None = None
    symbol: str
    status: str


class AgentJobResponse(BaseModel):
    job_id: UUID
    job_type: str
    status: str
    progress: list[AnalysisProgressEvent]
    result: AgentJobResult | None = None
    error_message: str | None = None


@router.get("/health")
def agent_gateway_health() -> dict[str, str]:
    return {"service": "AQuantLens Agent Gateway", "status": "ok"}


@router.get("/whoami")
def whoami(token: AgentTokenModel = Depends(get_current_agent_token)) -> dict[str, object]:
    return {
        "name": token.name,
        "token_prefix": token.token_prefix,
        "scopes": sorted(parse_csv(token.scopes)),
        "markets": parse_csv(token.markets),
        "instruments": parse_csv(token.instruments),
        "rate_limit_per_min": token.rate_limit_per_min,
        "status": token.status,
    }


def get_analysis_repository(session: Session = Depends(get_db_session)) -> AnalysisRepository:
    return AnalysisRepository(session)


@router.get("/reports", response_model=list[ReportListItem])
def list_reports(
    request: Request,
    token: AgentTokenModel = Depends(require_scope("R")),
    repository: AnalysisRepository = Depends(get_analysis_repository),
    session: Session = Depends(get_db_session),
) -> list[ReportListItem]:
    try:
        reports = [
            report
            for report in repository.list_reports()
            if list_matches(report.symbol, parse_csv(token.instruments))
        ]
    except HTTPException as exc:
        record_agent_audit(session, request=request, token=token, scope_class="R", status_code=exc.status_code, detail=str(exc.detail))
        raise
    record_agent_audit(session, request=request, token=token, scope_class="R", status_code=200)
    return reports


@router.post(
    "/jobs/research-analysis",
    response_model=AgentJobResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def submit_research_analysis_job(
    analysis_request: AnalysisRequest,
    request: Request,
    token: AgentTokenModel = Depends(require_scope("A")),
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
    repository: AnalysisRepository = Depends(get_analysis_repository),
    session: Session = Depends(get_db_session),
) -> AgentJobResponse:
    normalized_symbol = analysis_request.symbol.upper()
    try:
        ensure_instrument_allowed(token, normalized_symbol)
    except HTTPException as exc:
        record_agent_audit(session, request=request, token=token, scope_class="A", status_code=exc.status_code, detail=str(exc.detail))
        raise

    existing_job = get_idempotent_job(
        session,
        token=token,
        job_type=RESEARCH_ANALYSIS_JOB_TYPE,
        idempotency_key=idempotency_key,
    )
    if existing_job is not None:
        record_agent_audit(session, request=request, token=token, scope_class="A", status_code=202, detail="idempotent replay")
        return to_agent_job_response(existing_job)

    run = start_analysis_job(analysis_request, repository=repository)
    now = datetime.now(UTC)
    result = {
        "analysis_id": str(run.analysis_id),
        "report_id": str(run.report.report_id) if run.report else None,
        "symbol": run.request.symbol,
        "status": run.status,
    }
    job = AgentJobModel(
        agent_token_id=token.id,
        agent_name=token.name,
        job_type=RESEARCH_ANALYSIS_JOB_TYPE,
        idempotency_key=idempotency_key,
        status=run.status,
        request_json=run.request.model_dump(mode="json"),
        progress=[event.model_dump(mode="json") for event in run.progress],
        result_json=result,
        created_at=now,
        updated_at=now,
        completed_at=now if run.status == "completed" else None,
    )
    session.add(job)
    session.commit()
    session.refresh(job)
    record_agent_audit(session, request=request, token=token, scope_class="A", status_code=202)
    return to_agent_job_response(job)


@router.get("/jobs/{job_id}", response_model=AgentJobResponse)
def get_agent_job(
    job_id: UUID,
    request: Request,
    token: AgentTokenModel = Depends(require_scope("R")),
    session: Session = Depends(get_db_session),
) -> AgentJobResponse:
    job = get_owned_job(session, token=token, job_id=job_id)
    if job is None:
        record_agent_audit(session, request=request, token=token, scope_class="R", status_code=404, detail="job not found")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="job not found")
    record_agent_audit(session, request=request, token=token, scope_class="R", status_code=200)
    return to_agent_job_response(job)


@router.get("/jobs/{job_id}/result", response_model=AgentJobResult)
def get_agent_job_result(
    job_id: UUID,
    request: Request,
    token: AgentTokenModel = Depends(require_scope("R")),
    session: Session = Depends(get_db_session),
) -> AgentJobResult:
    job = get_owned_job(session, token=token, job_id=job_id)
    if job is None:
        record_agent_audit(session, request=request, token=token, scope_class="R", status_code=404, detail="job not found")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="job not found")
    if job.status != "completed" or job.result_json is None:
        record_agent_audit(session, request=request, token=token, scope_class="R", status_code=409, detail="job result is not ready")
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="job result is not ready")
    record_agent_audit(session, request=request, token=token, scope_class="R", status_code=200)
    return AgentJobResult(**job.result_json)


@router.get("/reports/{report_id}", response_model=ResearchReport)
def get_report(
    report_id: UUID,
    request: Request,
    token: AgentTokenModel = Depends(require_scope("R")),
    repository: AnalysisRepository = Depends(get_analysis_repository),
    session: Session = Depends(get_db_session),
) -> ResearchReport:
    report = repository.get_report(report_id)
    if report is None:
        record_agent_audit(session, request=request, token=token, scope_class="R", status_code=404, detail="report not found")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="report not found")
    try:
        ensure_instrument_allowed(token, report.symbol)
    except HTTPException as exc:
        record_agent_audit(session, request=request, token=token, scope_class="R", status_code=exc.status_code, detail=str(exc.detail))
        raise
    record_agent_audit(session, request=request, token=token, scope_class="R", status_code=200)
    return report


def get_idempotent_job(
    session: Session,
    *,
    token: AgentTokenModel,
    job_type: str,
    idempotency_key: str | None,
) -> AgentJobModel | None:
    if not idempotency_key:
        return None
    return session.scalar(
        select(AgentJobModel)
        .where(AgentJobModel.agent_token_id == token.id)
        .where(AgentJobModel.job_type == job_type)
        .where(AgentJobModel.idempotency_key == idempotency_key)
    )


def get_owned_job(session: Session, *, token: AgentTokenModel, job_id: UUID) -> AgentJobModel | None:
    return session.scalar(
        select(AgentJobModel)
        .where(AgentJobModel.id == job_id)
        .where(AgentJobModel.agent_token_id == token.id)
    )


def to_agent_job_response(job: AgentJobModel) -> AgentJobResponse:
    return AgentJobResponse(
        job_id=job.id,
        job_type=job.job_type,
        status=job.status,
        progress=[AnalysisProgressEvent(**event) for event in job.progress],
        result=AgentJobResult(**job.result_json) if job.result_json else None,
        error_message=job.error_message,
    )
