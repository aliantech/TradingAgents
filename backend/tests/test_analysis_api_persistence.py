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
    assert run["report_id"]


def test_analysis_api_persists_analyst_set_into_report_metadata():
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
    report_id = status_response.json()["report_id"]

    analysis_store._runs.clear()
    runs_response = client.get("/api/analysis/runs")
    run = next(item for item in runs_response.json()["runs"] if item["analysis_id"] == analysis_id)
    assert run["analyst_set"] == "full"

    report_response = client.get(f"/api/reports/{report_id}")
    assert report_response.status_code == 200
    report = report_response.json()
    assert report["analyst_set"] == "full"
    assert "研究团队：full" in report["markdown"]


def test_analysis_api_persists_research_template_into_run_and_report():
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
    report_id = status_response.json()["report_id"]

    analysis_store._runs.clear()
    runs_response = client.get("/api/analysis/runs")
    run = next(item for item in runs_response.json()["runs"] if item["analysis_id"] == analysis_id)
    assert run["research_template"] == "earnings-preview"

    report_response = client.get(f"/api/reports/{report_id}")
    assert report_response.status_code == 200
    report = report_response.json()
    assert report["research_template"] == "earnings-preview"
    assert "研究模板：earnings-preview" in report["markdown"]


def test_analysis_report_includes_evidence_labels_for_quality_review():
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
    report_response = client.get(f"/api/reports/{status_response.json()['report_id']}")

    assert report_response.status_code == 200
    report = report_response.json()
    assert report["evidence_labels"] == [
        "market-bars",
        "options-chain",
        "provider-readiness",
        "tradingagents-debate",
    ]
    assert "## 证据标签" in report["markdown"]
    assert "- options-chain" in report["markdown"]
