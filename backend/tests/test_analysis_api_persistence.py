from fastapi.testclient import TestClient

from app.analysis.store import analysis_store
from app.main import app


def test_analysis_api_persists_report_history_through_repository():
    client = TestClient(app)

    response = client.post(
        "/api/analysis",
        json={
            "symbol": "QQQ",
            "asset_type": "etf",
            "analysis_date": "2026-06-17",
            "language": "zh",
            "llm_provider": "openai",
            "model": "gpt-5.5",
            "depth": "standard",
        },
    )

    assert response.status_code == 202
    analysis_id = response.json()["analysis_id"]
    analysis_store._runs.clear()

    status_response = client.get(f"/api/analysis/{analysis_id}")
    assert status_response.status_code == 200
    report_id = status_response.json()["report_id"]

    reports_response = client.get("/api/reports")
    assert reports_response.status_code == 200
    assert any(report["report_id"] == report_id for report in reports_response.json())

    report_response = client.get(f"/api/reports/{report_id}")
    assert report_response.status_code == 200
    assert report_response.json()["symbol"] == "QQQ"
