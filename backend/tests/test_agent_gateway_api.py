from hashlib import sha256
from uuid import uuid4

from fastapi.testclient import TestClient

from app.analysis.service import start_analysis
from app.analysis.repository import AnalysisRepository
from app.analysis.schemas import AnalysisDepth, AnalysisRequest, AssetType, ReportLanguage
from app.db.models import AgentTokenModel
from app.db.session import SessionLocal, initialize_database
from app.main import app


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
        run = start_analysis(
            AnalysisRequest(
                symbol="SPY",
                asset_type=AssetType.etf,
                analysis_date="2026-06-19",
                language=ReportLanguage.zh,
                llm_provider="openai",
                model="gpt-5.5",
                depth=AnalysisDepth.standard,
            ),
            repository=AnalysisRepository(session),
        )
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


def seed_agent_token(*, scopes: str = "R,A", instruments: str = "SPY,QQQ") -> str:
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
                rate_limit_per_min=30,
                status="active",
            )
        )
        session.commit()
    finally:
        session.close()
    return raw_token
