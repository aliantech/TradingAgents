from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.agent_gateway.auth import get_current_agent_token, parse_csv, require_scope
from app.analysis.repository import AnalysisRepository
from app.db.models import AgentTokenModel
from app.db.session import get_db_session
from app.reports.schemas import ReportListItem, ResearchReport

router = APIRouter(prefix="/api/agent/v1", tags=["agent-gateway"])


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
    token: AgentTokenModel = Depends(require_scope("R")),
    repository: AnalysisRepository = Depends(get_analysis_repository),
) -> list[ReportListItem]:
    return repository.list_reports()


@router.get("/reports/{report_id}", response_model=ResearchReport)
def get_report(
    report_id: UUID,
    token: AgentTokenModel = Depends(require_scope("R")),
    repository: AnalysisRepository = Depends(get_analysis_repository),
) -> ResearchReport:
    report = repository.get_report(report_id)
    if report is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="report not found")
    return report
