from uuid import uuid4

from fastapi.testclient import TestClient

from app.analysis.store import analysis_store
from app.main import app


def test_report_comparison_has_no_mock_reports_for_analysis_runs():
    client = TestClient(app)
    symbol = f"T{uuid4().hex[:7]}".upper()

    response = client.post(
        "/api/analysis",
        json={
            "symbol": symbol,
            "asset_type": "etf",
            "analysis_date": "2026-06-17",
            "language": "zh",
            "llm_provider": "openai",
            "model": "gpt-5.5",
            "depth": "standard",
            "analyst_set": "macro-options",
        },
    )
    assert response.status_code == 202

    analysis_store._runs.clear()
    status_response = client.get(f"/api/analysis/{response.json()['analysis_id']}")
    reports_response = client.get("/api/reports")

    assert status_response.json()["report_id"] is not None
    report = next(report for report in reports_response.json() if report["symbol"] == symbol)
    assert report["analysis_id"] == response.json()["analysis_id"]


def test_report_comparison_returns_404_when_no_prior_symbol_report_exists():
    client = TestClient(app)
    symbol = f"T{uuid4().hex[:7]}".upper()

    response = client.post(
        "/api/analysis",
        json={
            "symbol": symbol,
            "asset_type": "equity",
            "analysis_date": "2026-06-18",
            "language": "zh",
            "llm_provider": "openai",
            "model": "gpt-5.5",
            "depth": "standard",
        },
    )
    assert response.status_code == 202
    analysis_store._runs.clear()
    comparison_response = client.get(f"/api/reports/{uuid4()}/comparison")

    assert comparison_response.status_code == 404
    assert comparison_response.json()["detail"] == "report not found"
