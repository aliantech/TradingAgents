from datetime import UTC, datetime, timedelta
from hashlib import sha256
from uuid import uuid4

from fastapi.testclient import TestClient

from app.agent_gateway.auth import RATE_LIMIT_BUCKETS
from app.analysis.repository import AnalysisRepository
from app.analysis.schemas import AnalysisDepth, AnalysisProgressEvent, AnalysisRequest, AssetType, ReportLanguage
from app.analysis.store import AnalysisRun
from app.db.models import AgentAuditModel, AgentTokenModel
from app.db.session import SessionLocal, initialize_database
from app.main import app
from app.reports.schemas import ResearchReport


def test_agent_gateway_whoami_requires_agent_token():
    client = TestClient(app)

    response = client.get("/api/agent/v1/whoami")

    assert response.status_code == 401
    assert response.json()["detail"] == "missing or malformed agent token"


def test_agent_gateway_whoami_returns_scoped_identity_without_token_value():
    initialize_database()
    raw_token = f"aql_agent_test_{uuid4().hex}"
    session = SessionLocal()
    try:
        session.add(
            AgentTokenModel(
                name="local-read-agent",
                token_prefix="aql_agent_test",
                token_hash=sha256(raw_token.encode("utf-8")).hexdigest(),
                scopes="R,A",
                markets="US",
                instruments="SPY,QQQ",
                rate_limit_per_min=30,
                status="active",
            )
        )
        session.commit()
    finally:
        session.close()

    client = TestClient(app)
    response = client.get("/api/agent/v1/whoami", headers={"Authorization": f"Bearer {raw_token}"})

    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "local-read-agent"
    assert body["token_prefix"] == "aql_agent_test"
    assert body["scopes"] == ["A", "R"]
    assert body["markets"] == ["US"]
    assert body["instruments"] == ["SPY", "QQQ"]
    assert "token" not in body
    assert raw_token not in response.text


def test_agent_gateway_reports_require_read_scope_and_return_research_reports():
    raw_token = seed_agent_token(scopes="R", instruments="SPY")
    session = SessionLocal()
    try:
        run = create_report(session, "SPY")
    finally:
        session.close()

    client = TestClient(app)
    headers = {"Authorization": f"Bearer {raw_token}"}

    list_response = client.get("/api/agent/v1/reports", headers=headers)
    detail_response = client.get(f"/api/agent/v1/reports/{run.report.report_id}", headers=headers)

    assert list_response.status_code == 200
    assert any(report["report_id"] == str(run.report.report_id) for report in list_response.json())
    assert detail_response.status_code == 200
    assert detail_response.json()["report_id"] == str(run.report.report_id)
    assert detail_response.json()["symbol"] == "SPY"


def test_agent_gateway_reports_reject_token_without_read_scope():
    raw_token = seed_agent_token(scopes="A")
    client = TestClient(app)

    response = client.get("/api/agent/v1/reports", headers={"Authorization": f"Bearer {raw_token}"})

    assert response.status_code == 403
    assert response.json()["detail"] == "agent token lacks required scope: R"


def test_agent_gateway_rejects_expired_token_and_records_denial_audit():
    raw_token = seed_agent_token(scopes="R", expires_at=datetime.now(UTC) - timedelta(minutes=1))
    client = TestClient(app)

    response = client.get("/api/agent/v1/reports", headers={"Authorization": f"Bearer {raw_token}"})

    assert response.status_code == 401
    assert response.json()["detail"] == "agent token expired"
    assert latest_audit_status("/api/agent/v1/reports") == 401


def test_agent_gateway_report_detail_enforces_instrument_allowlist_and_audits():
    allowed_token = seed_agent_token(scopes="R", instruments="SPY")
    session = SessionLocal()
    try:
        spy_run = create_report(session, "SPY")
        qqq_run = create_report(session, "QQQ")
    finally:
        session.close()

    client = TestClient(app)
    headers = {"Authorization": f"Bearer {allowed_token}"}

    allowed_response = client.get(f"/api/agent/v1/reports/{spy_run.report.report_id}", headers=headers)
    denied_response = client.get(f"/api/agent/v1/reports/{qqq_run.report.report_id}", headers=headers)

    assert allowed_response.status_code == 200
    assert denied_response.status_code == 403
    assert denied_response.json()["detail"] == "instrument not allowed: QQQ"
    assert audit_statuses(f"/api/agent/v1/reports/{spy_run.report.report_id}")[-1] == 200
    assert audit_statuses(f"/api/agent/v1/reports/{qqq_run.report.report_id}")[-1] == 403


def test_agent_gateway_report_list_filters_instrument_allowlist():
    allowed_token = seed_agent_token(scopes="R", instruments="SPY")
    session = SessionLocal()
    try:
        spy_run = create_report(session, "SPY")
        qqq_run = create_report(session, "QQQ")
    finally:
        session.close()

    client = TestClient(app)
    response = client.get("/api/agent/v1/reports", headers={"Authorization": f"Bearer {allowed_token}"})

    report_ids = {item["report_id"] for item in response.json()}
    assert response.status_code == 200
    assert str(spy_run.report.report_id) in report_ids
    assert str(qqq_run.report.report_id) not in report_ids


def test_agent_gateway_enforces_rate_limit_and_records_audit():
    RATE_LIMIT_BUCKETS.clear()
    raw_token = seed_agent_token(scopes="R", rate_limit_per_min=1)
    client = TestClient(app)
    headers = {"Authorization": f"Bearer {raw_token}"}

    first_response = client.get("/api/agent/v1/reports", headers=headers)
    second_response = client.get("/api/agent/v1/reports", headers=headers)

    assert first_response.status_code == 200
    assert second_response.status_code == 429
    assert second_response.json()["detail"] == "agent token rate limit exceeded"
    assert latest_audit_status("/api/agent/v1/reports") == 429


def test_agent_gateway_submits_and_polls_research_analysis_job():
    raw_token = seed_agent_token(scopes="R,A", instruments="SPY")
    client = TestClient(app)
    headers = {"Authorization": f"Bearer {raw_token}"}

    submit_response = client.post(
        "/api/agent/v1/jobs/research-analysis",
        headers=headers,
        json=analysis_payload("SPY"),
    )

    assert submit_response.status_code == 202
    submitted_job = submit_response.json()
    assert submitted_job["job_type"] == "research_analysis"
    assert submitted_job["status"] == "completed"
    assert submitted_job["result"]["symbol"] == "SPY"
    assert submitted_job["result"]["analysis_id"]
    assert submitted_job["result"]["report_id"] is not None
    assert any(event["step"] == "report" for event in submitted_job["progress"])

    poll_response = client.get(f"/api/agent/v1/jobs/{submitted_job['job_id']}", headers=headers)
    result_response = client.get(f"/api/agent/v1/jobs/{submitted_job['job_id']}/result", headers=headers)

    assert poll_response.status_code == 200
    assert poll_response.json()["job_id"] == submitted_job["job_id"]
    assert poll_response.json()["status"] == "completed"
    assert result_response.status_code == 200
    assert result_response.json()["report_id"] == submitted_job["result"]["report_id"]


def test_agent_gateway_replays_research_analysis_job_with_idempotency_key():
    raw_token = seed_agent_token(scopes="R,A", instruments="SPY")
    client = TestClient(app)
    headers = {
        "Authorization": f"Bearer {raw_token}",
        "Idempotency-Key": f"job-replay-{uuid4().hex}",
    }

    first_response = client.post(
        "/api/agent/v1/jobs/research-analysis",
        headers=headers,
        json=analysis_payload("SPY"),
    )
    second_response = client.post(
        "/api/agent/v1/jobs/research-analysis",
        headers=headers,
        json=analysis_payload("SPY"),
    )

    assert first_response.status_code == 202
    assert second_response.status_code == 202
    assert second_response.json()["job_id"] == first_response.json()["job_id"]
    assert second_response.json()["result"]["analysis_id"] == first_response.json()["result"]["analysis_id"]


def test_agent_gateway_research_analysis_job_requires_action_scope():
    raw_token = seed_agent_token(scopes="R", instruments="SPY")
    client = TestClient(app)

    response = client.post(
        "/api/agent/v1/jobs/research-analysis",
        headers={"Authorization": f"Bearer {raw_token}"},
        json=analysis_payload("SPY"),
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "agent token lacks required scope: A"


def test_agent_gateway_research_analysis_job_enforces_instrument_allowlist():
    raw_token = seed_agent_token(scopes="R,A", instruments="SPY")
    client = TestClient(app)

    response = client.post(
        "/api/agent/v1/jobs/research-analysis",
        headers={"Authorization": f"Bearer {raw_token}"},
        json=analysis_payload("QQQ"),
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "instrument not allowed: QQQ"
    assert latest_audit_status("/api/agent/v1/jobs/research-analysis") == 403


def analysis_payload(symbol: str) -> dict[str, str]:
    return {
        "symbol": symbol,
        "asset_type": "etf",
        "analysis_date": "2026-06-19",
        "language": "zh",
        "llm_provider": "openai",
        "model": "gpt-5.5",
        "depth": "standard",
        "analyst_set": "macro-options",
        "research_template": "general",
    }


def create_report(session, symbol: str):
    analysis_id = uuid4()
    report_id = uuid4()
    request = AnalysisRequest(
        symbol=symbol,
        asset_type=AssetType.etf,
        analysis_date="2026-06-19",
        language=ReportLanguage.zh,
        llm_provider="openai",
        model="gpt-5.5",
        depth=AnalysisDepth.standard,
    )
    report = ResearchReport(
        report_id=report_id,
        analysis_id=analysis_id,
        symbol=symbol,
        language=ReportLanguage.zh,
        analyst_set="macro-options",
        research_template="general",
        summary=f"{symbol} persisted test report",
        market_background="Persisted report fixture.",
        fundamental_analysis="Persisted report fixture.",
        technical_analysis="Persisted report fixture.",
        sentiment_analysis="Persisted report fixture.",
        options_observation="Persisted report fixture.",
        bull_case="Persisted report fixture.",
        bear_case="Persisted report fixture.",
        risk_factors=[],
        evidence_labels=["persisted-report"],
        trade_plan="Research only.",
        position_sizing="Research only.",
        take_profit_stop_loss="Research only.",
        confidence=0.5,
        markdown=f"# {symbol} persisted test report",
    )
    run = AnalysisRun(
        analysis_id=analysis_id,
        request=request,
        status="completed",
        progress=[AnalysisProgressEvent(step="report", status="completed", message="persisted report fixture")],
        report=report,
    )
    AnalysisRepository(session).save_run(run)
    return run


def latest_audit_status(route: str) -> int:
    statuses = audit_statuses(route)
    assert statuses
    return statuses[-1]


def audit_statuses(route: str) -> list[int]:
    session = SessionLocal()
    try:
        rows = (
            session.query(AgentAuditModel)
            .filter(AgentAuditModel.route == route)
            .order_by(AgentAuditModel.created_at.asc())
            .all()
        )
        return [row.status_code for row in rows]
    finally:
        session.close()


def seed_agent_token(
    *,
    scopes: str = "R,A",
    instruments: str = "SPY,QQQ",
    expires_at=None,
    rate_limit_per_min: int = 30,
) -> str:
    initialize_database()
    raw_token = f"aql_agent_test_{uuid4().hex}"
    session = SessionLocal()
    try:
        session.add(
            AgentTokenModel(
                name=f"test-agent-{uuid4().hex[:8]}",
                token_prefix="aql_agent_test",
                token_hash=sha256(raw_token.encode("utf-8")).hexdigest(),
                scopes=scopes,
                markets="US",
                instruments=instruments,
                rate_limit_per_min=rate_limit_per_min,
                status="active",
                expires_at=expires_at,
            )
        )
        session.commit()
    finally:
        session.close()
    return raw_token
