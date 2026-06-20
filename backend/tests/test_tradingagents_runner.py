from datetime import date
from uuid import uuid4

import pytest

from app.analysis.schemas import AnalysisDepth, AnalysisRequest, AssetType, ReportLanguage, ResearchTemplate
from app.analysis.tradingagents_adapter import build_tradingagents_request
from app.analysis.tradingagents_runner import (
    REAL_TRADINGAGENTS_MODE,
    build_real_tradingagents_config,
    parse_selected_analysts,
    run_configured_research,
    run_real_tradingagents_research,
    tradingagents_state_to_result,
)
from app.core.config import Settings


def test_configured_runner_defaults_to_deterministic_without_real_provider_call(monkeypatch):
    execution_request = build_tradingagents_request(uuid4(), analysis_request())

    def fail_if_called(*args, **kwargs):
        raise AssertionError("real TradingAgents runner should not be called")

    monkeypatch.setattr("app.analysis.tradingagents_runner.run_real_tradingagents_research", fail_if_called)

    result = run_configured_research(execution_request, Settings(tradingagents_runner_mode="deterministic"))

    assert result.report.evidence_labels == ["deterministic-tradingagents-fixture"]
    assert result.progress[-1].status == "completed"


def test_real_runner_requires_explicit_runtime_gate():
    execution_request = build_tradingagents_request(uuid4(), analysis_request())

    with pytest.raises(RuntimeError, match="disabled"):
        run_real_tradingagents_research(execution_request, Settings(tradingagents_runner_mode="deterministic"))


def test_real_runner_config_reads_runtime_settings():
    execution_request = build_tradingagents_request(uuid4(), analysis_request())
    runtime_settings = Settings(
        tradingagents_runner_mode=REAL_TRADINGAGENTS_MODE,
        tradingagents_llm_provider="anthropic",
        tradingagents_deep_think_llm="claude-opus-4",
        tradingagents_quick_think_llm="claude-sonnet-4",
        tradingagents_output_language="Chinese",
        tradingagents_max_debate_rounds=2,
        tradingagents_max_risk_discuss_rounds=3,
    )

    config = build_real_tradingagents_config(execution_request, runtime_settings)

    assert config["llm_provider"] == "anthropic"
    assert config["deep_think_llm"] == "claude-opus-4"
    assert config["quick_think_llm"] == "claude-sonnet-4"
    assert config["output_language"] == "Chinese"
    assert config["max_debate_rounds"] == 2
    assert config["max_risk_discuss_rounds"] == 3
    assert config["checkpoint_enabled"] is False


def test_real_tradingagents_state_maps_to_adapter_result():
    execution_request = build_tradingagents_request(uuid4(), analysis_request(symbol="QQQ"))
    final_state = {
        "market_report": "market state",
        "fundamentals_report": "fundamentals state",
        "sentiment_report": "sentiment state",
        "news_report": "news state",
        "investment_debate_state": {
            "bull_history": "bull state",
            "bear_history": "bear state",
        },
    }

    result = tradingagents_state_to_result(execution_request, final_state, "final decision")

    assert result.report.summary.startswith("QQQ 中文 AI 投研摘要")
    assert result.report.market_background == "market state"
    assert result.report.fundamental_analysis == "fundamentals state"
    assert result.report.bull_case == "bull state"
    assert result.report.bear_case == "bear state"
    assert result.report.trade_plan == "final decision"
    assert result.report.evidence_labels == ["tradingagents-real-runner"]


def test_selected_analysts_parser_uses_safe_default_for_empty_value():
    assert parse_selected_analysts("") == ["market", "news", "fundamentals"]
    assert parse_selected_analysts("market, news") == ["market", "news"]


def analysis_request(symbol="SPY"):
    return AnalysisRequest(
        symbol=symbol,
        asset_type=AssetType.etf,
        analysis_date=date(2026, 6, 20),
        language=ReportLanguage.zh,
        llm_provider="openai",
        model="gpt-5.5",
        depth=AnalysisDepth.standard,
        analyst_set="macro-options",
        research_template=ResearchTemplate.general,
    )
