from uuid import uuid4

from fastapi.testclient import TestClient

from app.analysis.store import analysis_store
from app.main import app


def test_report_comparison_returns_previous_report_for_same_symbol():
    client = TestClient(app)
    symbol = f"T{uuid4().hex[:7]}".upper()

    first_response = client.post(
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
    second_response = client.post(
        "/api/analysis",
        json={
            "symbol": symbol,
            "asset_type": "etf",
            "analysis_date": "2026-06-18",
            "language": "zh",
            "llm_provider": "openai",
            "model": "gpt-5.5",
            "depth": "deep",
            "analyst_set": "full",
        },
    )
    assert first_response.status_code == 202
    assert second_response.status_code == 202

    analysis_store._runs.clear()
    current_status = client.get(f"/api/analysis/{second_response.json()['analysis_id']}")
    previous_status = client.get(f"/api/analysis/{first_response.json()['analysis_id']}")

    comparison_response = client.get(f"/api/reports/{current_status.json()['report_id']}/comparison")

    assert comparison_response.status_code == 200
    comparison = comparison_response.json()
    assert comparison["current"]["report_id"] == current_status.json()["report_id"]
    assert comparison["previous"]["report_id"] == previous_status.json()["report_id"]
    assert comparison["symbol"] == symbol
    assert comparison["confidence_delta"] == 0
    assert comparison["risk_factor_changes"] == {"added": [], "removed": []}
    assert comparison["section_changes"]["summary"]["changed"] is False


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
    status_response = client.get(f"/api/analysis/{response.json()['analysis_id']}")

    comparison_response = client.get(f"/api/reports/{status_response.json()['report_id']}/comparison")

    assert comparison_response.status_code == 404
    assert comparison_response.json()["detail"] == "previous report not found"
