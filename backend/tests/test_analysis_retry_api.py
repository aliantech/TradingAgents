from datetime import date
from uuid import uuid4

from fastapi.testclient import TestClient

from app.analysis.repository import AnalysisRepository
from app.analysis.schemas import AnalysisDepth, AnalysisProgressEvent, AnalysisRequest, AssetType, ReportLanguage
from app.analysis.store import AnalysisRun, analysis_store
from app.db.session import SessionLocal, initialize_database
from app.main import app


def test_analysis_retry_creates_new_run_from_failed_run():
    initialize_database()
    analysis_id = uuid4()
    request = AnalysisRequest(
        symbol="AAPL",
        asset_type=AssetType.equity,
        analysis_date=date(2026, 6, 19),
        language=ReportLanguage.zh,
        llm_provider="openai",
        model="gpt-5.5",
        depth=AnalysisDepth.standard,
        analyst_set="macro-options",
        research_template="technical-setup",
    )
    failed_run = AnalysisRun(
        analysis_id=analysis_id,
        request=request,
        status="failed",
        progress=[AnalysisProgressEvent(step="report", status="failed", message="provider timeout")],
    )
    session = SessionLocal()
    try:
        AnalysisRepository(session).save_run(failed_run)
    finally:
        session.close()

    analysis_store._runs.clear()
    client = TestClient(app)

    retry_response = client.post(f"/api/analysis/{analysis_id}/retry")

    assert retry_response.status_code == 202
    retry = retry_response.json()
    assert retry["analysis_id"] != str(analysis_id)
    assert retry["symbol"] == "AAPL"
    assert retry["status"] == "queued"

    retried_status = client.get(f"/api/analysis/{retry['analysis_id']}")
    assert retried_status.status_code == 200
    assert retried_status.json()["status"] == "completed"

    original_status = client.get(f"/api/analysis/{analysis_id}")
    assert original_status.status_code == 200
    assert original_status.json()["status"] == "failed"

    runs_response = client.get("/api/analysis/runs")
    retried_run = next(run for run in runs_response.json()["runs"] if run["analysis_id"] == retry["analysis_id"])
    assert retried_run["research_template"] == "technical-setup"


def test_analysis_retry_rejects_completed_run():
    client = TestClient(app)
    response = client.post(
        "/api/analysis",
        json={
            "symbol": "MSFT",
            "asset_type": "equity",
            "analysis_date": "2026-06-19",
            "language": "zh",
            "llm_provider": "openai",
            "model": "gpt-5.5",
            "depth": "standard",
        },
    )
    assert response.status_code == 202

    retry_response = client.post(f"/api/analysis/{response.json()['analysis_id']}/retry")

    assert retry_response.status_code == 409
    assert retry_response.json()["detail"] == "only failed analysis runs can be retried"
