from datetime import UTC, date, datetime

from fastapi.testclient import TestClient

from app.analysis import option_chain_context
from app.analysis.schemas import AnalysisProgressEvent
from app.analysis.store import analysis_store
from app.analysis.tradingagents_adapter import TradingAgentsReportPayload, TradingAgentsRunResult
from app.db.session import SessionLocal, initialize_database
from app.main import app
from app.options.repository import OptionContractRecord, OptionRepository, OptionSnapshotRecord


def _force_hub_unavailable(*args, **kwargs):
    raise option_chain_context.FinanceDataHubError("FDH disabled for persisted fallback test.")


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
    assert status_payload["failure_diagnostic"]["category"] == "runtime"
    assert status_payload["failure_diagnostic"]["failed_step"] == "tradingagents"
    assert "retry" in status_payload["failure_diagnostic"]["retry_guidance"].lower()


def test_analysis_api_rejects_invalid_report_quality_before_persistence(monkeypatch):
    def invalid_runner(*args, **kwargs):
        return TradingAgentsRunResult(
            progress=[AnalysisProgressEvent(step="tradingagents", status="completed", message="done")],
            report=TradingAgentsReportPayload(
                summary="SPY English summary",
                market_background="English market background",
                fundamental_analysis="English fundamentals",
                technical_analysis="English technicals",
                sentiment_analysis="English sentiment",
                options_observation="English options",
                bull_case="English bull",
                bear_case="English bear",
                risk_factors=["risk"],
                evidence_labels=[],
                trade_plan="Buy now.",
                position_sizing="Full size.",
                take_profit_stop_loss="Stop later.",
                confidence=0.5,
            ),
        )

    monkeypatch.setattr("app.analysis.service.run_configured_research", invalid_runner)
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
            "research_template": "general",
        },
    )

    assert response.status_code == 202
    status_response = client.get(f"/api/analysis/{response.json()['analysis_id']}")
    status_payload = status_response.json()
    assert status_payload["status"] == "failed"
    assert status_payload["report_id"] is None
    assert status_payload["progress"][-1]["step"] == "report_quality"
    assert "Report quality validation failed" in status_payload["progress"][-1]["message"]
    assert status_payload["failure_diagnostic"]["category"] == "report_quality"

    analysis_store._runs.clear()
    runs_response = client.get("/api/analysis/runs")
    run = next(item for item in runs_response.json()["runs"] if item["analysis_id"] == response.json()["analysis_id"])
    assert run["failure_diagnostic"]["category"] == "report_quality"


def test_analysis_api_passes_persisted_option_chain_context_to_runner(monkeypatch):
    monkeypatch.setattr(option_chain_context, "_build_finance_data_hub_context", _force_hub_unavailable)
    initialize_database()
    session = SessionLocal()
    try:
        repository = OptionRepository(session)
        repository.upsert_contract(
            OptionContractRecord(
                option_symbol="SPY260619P00740000",
                underlying_symbol="SPY",
                expiry=date(2026, 6, 19),
                strike=740.0,
                option_type="put",
                exercise_style="american",
                expiration_type="weekly",
                source="finance_data_hub",
            )
        )
        repository.upsert_snapshot(
            OptionSnapshotRecord(
                option_symbol="SPY260619P00740000",
                underlying_symbol="SPY",
                timestamp=datetime(2026, 6, 18, 20, 0, tzinfo=UTC),
                bid=4.2,
                ask=4.4,
                last=4.3,
                volume=220,
                open_interest=5800,
                implied_volatility=0.19,
                delta=-0.42,
                gamma=0.024,
                theta=-0.09,
                vega=0.21,
                source="finance_data_hub",
            )
        )
    finally:
        session.close()

    captured_context = {}

    def mocked_runner(execution_request, runtime_settings):
        captured_context["value"] = execution_request.option_chain_context
        return TradingAgentsRunResult(
            progress=[AnalysisProgressEvent(step="tradingagents", status="completed", message="done")],
            report=TradingAgentsReportPayload(
                summary="SPY 中文 AI 投研摘要",
                market_background="中文市场背景",
                fundamental_analysis="中文基本面分析",
                technical_analysis="中文技术分析",
                sentiment_analysis="中文情绪分析",
                options_observation=f"中文期权观察\n{execution_request.option_chain_context}",
                bull_case="中文多头情景",
                bear_case="中文空头情景",
                risk_factors=["模型输出不确定性"],
                evidence_labels=["deterministic-tradingagents-fixture"],
                trade_plan="仅用于研究复盘，不生成自动交易指令。",
                position_sizing="研究阶段不生成实盘仓位。",
                take_profit_stop_loss="风控参考仅用于研究复盘，不代表交易执行建议。",
                confidence=0.5,
                markdown="SPY 中文 AI 投研报告",
            ),
        )

    monkeypatch.setattr("app.analysis.service.run_configured_research", mocked_runner)
    client = TestClient(app)

    response = client.post(
        "/api/analysis",
        json={
            "symbol": "SPY",
            "asset_type": "etf",
            "analysis_date": "2026-06-18",
            "language": "zh",
            "llm_provider": "openai",
            "model": "gpt-5.5",
            "depth": "standard",
            "analyst_set": "macro-options",
            "research_template": "general",
        },
    )

    assert response.status_code == 202
    assert "逐合约期权链快照" in captured_context["value"]
    assert "SPY260619P00740000" in captured_context["value"]
