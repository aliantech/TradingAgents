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


def test_phase_one_analysis_flow_does_not_create_mock_report():
    client = TestClient(app)
    queued = _start_spy_analysis(client)

    status_response = client.get(f"/api/analysis/{queued['analysis_id']}")
    assert status_response.status_code == 200
    status_payload = status_response.json()
    assert status_payload["symbol"] == "SPY"
    assert status_payload["status"] == "completed"
    assert status_payload["report_id"] is not None
    assert len(status_payload["progress"]) >= 3

    reports_response = client.get("/api/reports")
    assert reports_response.status_code == 200
    reports = reports_response.json()
    report = next(report for report in reports if report["analysis_id"] == queued["analysis_id"])
    assert report["summary"].startswith("SPY 中文 AI 投研摘要")


def test_phase_one_market_and_options_context():
    client = TestClient(app)

    bars_response = client.get("/api/market-data/bars?symbol=SPY&timeframe=1m")
    assert bars_response.status_code == 200
    bars = bars_response.json()
    assert bars["symbol"] == "SPY"
    assert bars["timeframe"] == "1m"
    assert bars["bars"] == []

    chain_response = client.get("/api/options/chain?underlying=SPX&expiry=2026-06-26")
    assert chain_response.status_code == 200
    chain = chain_response.json()
    assert chain["underlying_symbol"] == "SPX"
    assert chain["expiry"] == "2026-06-26"
    assert chain["snapshots"] == []


def test_phase_one_progress_events_stream():
    client = TestClient(app)
    queued = _start_spy_analysis(client)

    response = client.get(f"/api/analysis/{queued['analysis_id']}/events")
    assert response.status_code == 200
    assert "text/event-stream" in response.headers["content-type"]
    assert "中文研究报告已生成并准备持久化" in response.text
