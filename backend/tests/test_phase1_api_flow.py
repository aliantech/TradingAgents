from fastapi.testclient import TestClient

from app.main import app


def _start_spy_analysis(client: TestClient) -> dict:
    response = client.post(
        "/api/analysis",
        json={
            "symbol": "spy",
            "asset_type": "etf",
            "analysis_date": "2026-06-17",
            "language": "zh",
            "llm_provider": "openai",
            "model": "gpt-5.5",
            "depth": "standard",
        },
    )
    assert response.status_code == 202
    return response.json()


def test_phase_one_analysis_report_flow():
    client = TestClient(app)
    queued = _start_spy_analysis(client)

    status_response = client.get(f"/api/analysis/{queued['analysis_id']}")
    assert status_response.status_code == 200
    status_payload = status_response.json()
    assert status_payload["symbol"] == "SPY"
    assert status_payload["status"] == "completed"
    assert status_payload["report_id"]
    assert len(status_payload["progress"]) >= 4

    reports_response = client.get("/api/reports")
    assert reports_response.status_code == 200
    reports = reports_response.json()
    assert any(report["report_id"] == status_payload["report_id"] for report in reports)

    report_response = client.get(f"/api/reports/{status_payload['report_id']}")
    assert report_response.status_code == 200
    report = report_response.json()
    assert report["language"] == "zh"
    assert "不构成投资建议" in report["markdown"]
    assert "期权" in report["options_observation"]


def test_phase_one_market_and_options_context():
    client = TestClient(app)

    bars_response = client.get("/api/market-data/bars?symbol=SPY&timeframe=1m")
    assert bars_response.status_code == 200
    bars = bars_response.json()
    assert bars["symbol"] == "SPY"
    assert bars["timeframe"] == "1m"
    assert len(bars["bars"]) >= 5

    chain_response = client.get("/api/options/chain?underlying=SPX&expiry=2026-06-17")
    assert chain_response.status_code == 200
    chain = chain_response.json()
    assert chain["underlying_symbol"] == "SPX"
    assert chain["expiry"] == "2026-06-17"
    assert len(chain["snapshots"]) >= 5
    assert "delta" in chain["snapshots"][0]


def test_phase_one_progress_events_stream():
    client = TestClient(app)
    queued = _start_spy_analysis(client)

    response = client.get(f"/api/analysis/{queued['analysis_id']}/events")
    assert response.status_code == 200
    assert "text/event-stream" in response.headers["content-type"]
    assert "中文结构化报告已生成" in response.text
