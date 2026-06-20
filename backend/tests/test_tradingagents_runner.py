from datetime import date
from uuid import uuid4

import pytest

from app.analysis.schemas import AnalysisDepth, AnalysisRequest, AssetType, ReportLanguage, ResearchTemplate
from app.analysis.tradingagents_adapter import build_tradingagents_request, tradingagents_result_to_report
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
    assert config["tool_vendors"]["get_stock_data"] == "direct_yahoo_chart"


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


def test_real_tradingagents_mapped_report_passes_quality_contract():
    execution_request = build_tradingagents_request(uuid4(), analysis_request(symbol="QQQ"))
    result = tradingagents_state_to_result(
        execution_request,
        {
            "market_report": "市场报告覆盖趋势、成交量和关键风险。",
            "fundamentals_report": "基本面报告覆盖盈利、估值和流动性。",
            "sentiment_report": "情绪报告覆盖新闻叙事和风险偏好。",
            "news_report": "新闻报告覆盖宏观事件和公司催化。",
            "investment_debate_state": {
                "bull_history": "多头情景关注趋势延续和流动性改善。",
                "bear_history": "空头情景关注波动率扩张和宏观冲击。",
            },
        },
        "研究结论仅用于复盘观察，不生成自动交易指令。",
    )

    report = tradingagents_result_to_report(
        execution_request=execution_request,
        result=result,
        report_id=uuid4(),
    )

    assert report.evidence_labels == ["tradingagents-real-runner"]
    assert report.report_id is not None


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
