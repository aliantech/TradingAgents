from fastapi.testclient import TestClient

from app.main import app


def test_start_analysis_accepts_phase_one_payload():
    client = TestClient(app)
    response = client.post(
        "/api/analysis",
        json={
            "symbol": "SPY",
            "asset_type": "etf",
            "analysis_date": "2026-06-17",
            "language": "zh",
            "llm_provider": "openai",
            "model": "gpt-5.5",
            "depth": "standard",
        },
    )

    assert response.status_code == 202
    payload = response.json()
    assert payload["symbol"] == "SPY"
    assert payload["status"] == "queued"
    assert payload["language"] == "zh"
    assert isinstance(payload["analysis_id"], str)
