from datetime import date

from app.analysis.cli import real_runner_smoke_missing_prerequisites, run_real_runner_smoke
from app.analysis.schemas import AnalysisDepth, AnalysisProgressEvent, AnalysisRequest, AssetType, ReportLanguage, ResearchTemplate
from app.analysis.tradingagents_adapter import TradingAgentsReportPayload, TradingAgentsRunResult
from app.analysis.tradingagents_runner import REAL_TRADINGAGENTS_MODE
from app.core.config import Settings


def test_real_runner_smoke_requires_confirmation_and_real_runner_mode():
    missing = real_runner_smoke_missing_prerequisites(
        runtime_settings=Settings(tradingagents_runner_mode="deterministic", tradingagents_llm_provider="openai"),
        explicit_confirmation=False,
        environ={"OPENAI_API_KEY": "present"},
    )

    assert "--i-understand-this-calls-a-real-llm-provider" in missing
    assert "AQUANTLENS_TRADINGAGENTS_RUNNER_MODE=real-tradingagents" in missing


def test_real_runner_smoke_requires_provider_key_without_printing_value():
    missing = real_runner_smoke_missing_prerequisites(
        runtime_settings=Settings(tradingagents_runner_mode=REAL_TRADINGAGENTS_MODE, tradingagents_llm_provider="openai"),
        explicit_confirmation=True,
        environ={},
    )

    assert missing == ["OPENAI_API_KEY"]


def test_real_runner_smoke_stops_before_runner_when_not_ready(monkeypatch):
    def fail_if_called(*args, **kwargs):
        raise AssertionError("real runner should not be called before readiness passes")

    monkeypatch.setattr("app.analysis.cli.run_configured_research", fail_if_called)

    result = run_real_runner_smoke(
        runtime_settings=Settings(tradingagents_runner_mode="deterministic", tradingagents_llm_provider="openai"),
        request=analysis_request(),
        explicit_confirmation=False,
        environ={},
    )

    assert result.status == "not_ready"
    assert result.report_generated is False
    assert result.missing


def test_real_runner_smoke_runs_mocked_real_runner_after_gate_passes(monkeypatch):
    def mocked_runner(execution_request, runtime_settings):
        return TradingAgentsRunResult(
            progress=[AnalysisProgressEvent(step="tradingagents", status="completed", message="done")],
            report=TradingAgentsReportPayload(
                summary="summary",
                market_background="market",
                fundamental_analysis="fundamental",
                technical_analysis="technical",
                sentiment_analysis="sentiment",
                options_observation="options",
                bull_case="bull",
                bear_case="bear",
                risk_factors=["risk"],
                evidence_labels=["tradingagents-real-runner"],
                trade_plan="research only",
                position_sizing="none",
                take_profit_stop_loss="none",
                confidence=0.5,
            ),
        )

    monkeypatch.setattr("app.analysis.cli.run_configured_research", mocked_runner)

    result = run_real_runner_smoke(
        runtime_settings=Settings(tradingagents_runner_mode=REAL_TRADINGAGENTS_MODE, tradingagents_llm_provider="openai"),
        request=analysis_request(),
        explicit_confirmation=True,
        environ={"OPENAI_API_KEY": "sk-not-printed"},
    )

    assert result.status == "succeeded"
    assert result.report_generated is True
    assert result.evidence_labels == ["tradingagents-real-runner"]


def test_real_runner_smoke_redacts_runner_errors_through_adapter_path(monkeypatch):
    def failing_runner(*args, **kwargs):
        raise RuntimeError("provider failed api_key=sk-secret Bearer abc123")

    monkeypatch.setattr("app.analysis.cli.run_configured_research", failing_runner)

    result = run_real_runner_smoke(
        runtime_settings=Settings(tradingagents_runner_mode=REAL_TRADINGAGENTS_MODE, tradingagents_llm_provider="openai"),
        request=analysis_request(),
        explicit_confirmation=True,
        environ={"OPENAI_API_KEY": "sk-not-printed"},
    )

    assert result.status == "failed"
    assert "[redacted]" in result.error_message
    assert "sk-secret" not in result.error_message
    assert "abc123" not in result.error_message


def analysis_request():
    return AnalysisRequest(
        symbol="SPY",
        asset_type=AssetType.etf,
        analysis_date=date(2026, 6, 20),
        language=ReportLanguage.zh,
        llm_provider="openai",
        model="gpt-5.5",
        depth=AnalysisDepth.standard,
        analyst_set="macro-options",
        research_template=ResearchTemplate.general,
    )
