from fastapi.testclient import TestClient

from app.analysis.store import analysis_store
from app.main import app


def test_analysis_api_persists_completed_deterministic_report():
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
    status_payload = status_response.json()
    assert status_payload["status"] == "completed"
    assert status_payload["report_id"] is not None
    assert status_payload["progress"][-1]["status"] == "completed"

    reports_response = client.get("/api/reports")
    assert reports_response.status_code == 200
    report_item = next(report for report in reports_response.json() if report["analysis_id"] == analysis_id)
    assert report_item["symbol"] == "QQQ"
    assert report_item["summary"].startswith("QQQ 中文 AI 投研摘要")

    report_response = client.get(f"/api/reports/{status_payload['report_id']}")
    assert report_response.status_code == 200
    report_payload = report_response.json()
    assert report_payload["analysis_id"] == analysis_id
    assert report_payload["language"] == "zh"
    assert report_payload["evidence_labels"] == ["deterministic-tradingagents-fixture"]
    assert "样例" not in report_payload["markdown"]


def test_analysis_api_lists_persisted_runs_for_task_center():
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
            "depth": "deep",
        },
    )

    assert response.status_code == 202
    analysis_id = response.json()["analysis_id"]
    analysis_store._runs.clear()

    runs_response = client.get("/api/analysis/runs")
    assert runs_response.status_code == 200
    runs = runs_response.json()["runs"]
    run = next(item for item in runs if item["analysis_id"] == analysis_id)
    assert run["symbol"] == "SPY"
    assert run["status"] == "completed"
    assert run["llm_provider"] == "openai"
    assert run["model"] == "gpt-5.5"
    assert run["depth"] == "deep"
    assert run["analyst_set"] == "macro-options"
    assert run["created_at"]
    assert run["updated_at"]
    assert run["report_id"] is not None


def test_analysis_api_persists_analyst_set_without_report_metadata():
    client = TestClient(app)

    response = client.post(
        "/api/analysis",
        json={
            "symbol": "SPX",
            "asset_type": "index",
            "analysis_date": "2026-06-17",
            "language": "zh",
            "llm_provider": "openai",
            "model": "gpt-5.5",
            "depth": "standard",
            "analyst_set": "full",
        },
    )

    assert response.status_code == 202
    analysis_id = response.json()["analysis_id"]
    status_response = client.get(f"/api/analysis/{analysis_id}")
    assert status_response.json()["report_id"] is not None

    analysis_store._runs.clear()
    runs_response = client.get("/api/analysis/runs")
    run = next(item for item in runs_response.json()["runs"] if item["analysis_id"] == analysis_id)
    assert run["analyst_set"] == "full"


def test_analysis_api_persists_research_template_into_run_without_report():
    client = TestClient(app)

    response = client.post(
        "/api/analysis",
        json={
            "symbol": "NVDA",
            "asset_type": "equity",
            "analysis_date": "2026-06-19",
            "language": "zh",
            "llm_provider": "openai",
            "model": "gpt-5.5",
            "depth": "standard",
            "analyst_set": "macro-options",
            "research_template": "earnings-preview",
        },
    )

    assert response.status_code == 202
    analysis_id = response.json()["analysis_id"]
    status_response = client.get(f"/api/analysis/{analysis_id}")
    assert status_response.json()["report_id"] is not None

    analysis_store._runs.clear()
    runs_response = client.get("/api/analysis/runs")
    run = next(item for item in runs_response.json()["runs"] if item["analysis_id"] == analysis_id)
    assert run["research_template"] == "earnings-preview"


def test_analysis_does_not_emit_mock_report_evidence_labels():
    client = TestClient(app)

    response = client.post(
        "/api/analysis",
        json={
            "symbol": "SPY",
            "asset_type": "etf",
            "analysis_date": "2026-06-19",
            "language": "zh",
            "llm_provider": "openai",
            "model": "gpt-5.5",
            "depth": "standard",
            "analyst_set": "macro-options",
            "research_template": "macro-options-readthrough",
        },
    )

    assert response.status_code == 202
    status_response = client.get(f"/api/analysis/{response.json()['analysis_id']}")
    assert status_response.json()["report_id"] is not None

    report_response = client.get(f"/api/reports/{status_response.json()['report_id']}")
    assert report_response.status_code == 200
    assert "AQuantLens Phase 1 sample report" not in report_response.json()["evidence_labels"]


def test_analysis_api_persists_failed_run_without_report_when_fixture_fails():
    client = TestClient(app)

    response = client.post(
        "/api/analysis",
        json={
            "symbol": "FAIL",
            "asset_type": "equity",
            "analysis_date": "2026-06-19",
            "language": "zh",
            "llm_provider": "openai",
            "model": "gpt-5.5",
            "depth": "standard",
            "analyst_set": "macro-options",
            "research_template": "general",
        },
    )

    assert response.status_code == 202
    status_response = client.get(f"/api/analysis/{response.json()['analysis_id']}")
    assert status_response.status_code == 200
    status_payload = status_response.json()
    assert status_payload["status"] == "failed"
    assert status_payload["report_id"] is None
    assert status_payload["progress"][-1]["step"] == "tradingagents"
    assert status_payload["progress"][-1]["status"] == "failed"
