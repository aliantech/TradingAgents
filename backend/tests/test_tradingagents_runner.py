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


SNAPSHOT_FIXTURE = (
    "## Verified market data snapshot for QQQ\n\n"
    "- Latest trading row used: 2026-06-20\n\n"
    "### Latest verified OHLCV row\n\n"
    "| Field | Value |\n"
    "|---|---:|\n"
    "| Close | 512.34 |"
)


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
    assert config["tool_vendors"]["get_macro_indicators"] == "macro_unavailable"
    assert config["finance_data_hub_base_url"] == "http://127.0.0.1:18180"
    assert config["tool_vendors"]["get_indicators"] == "finance_data_hub"
    assert config["tool_vendors"]["get_stock_data"] == "finance_data_hub"


def test_real_tradingagents_state_maps_to_adapter_result(monkeypatch):
    monkeypatch.setattr(
        "app.analysis.tradingagents_runner.build_runner_verified_market_snapshot",
        lambda symbol, analysis_date: SNAPSHOT_FIXTURE,
    )
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
    assert "Latest trading row used: 2026-06-20" in result.report.market_background
    assert "market state" in result.report.market_background
    assert result.report.fundamental_analysis == "fundamentals state"
    assert result.report.bull_case == "bull state"
    assert result.report.bear_case == "bear state"
    assert "原始 TradingAgents 结论：final decision" in result.report.trade_plan
    assert "观察条件" in result.report.trade_plan
    assert "风险边界" in result.report.trade_plan
    assert "仅用于研究复盘" in result.report.trade_plan
    assert result.report.evidence_labels == ["tradingagents-real-runner", "finance-data-hub-verified-snapshot"]


def test_real_tradingagents_mapping_expands_one_word_decision_and_options_observation(monkeypatch):
    monkeypatch.setattr(
        "app.analysis.tradingagents_runner.build_runner_verified_market_snapshot",
        lambda symbol, analysis_date: SNAPSHOT_FIXTURE,
    )
    execution_request = build_tradingagents_request(uuid4(), analysis_request(symbol="SPY"))
    execution_request = execution_request.model_copy(
        update={
            "option_chain_context": (
                "逐合约期权链快照（持久化数据）：SPY 最近到期日 2026-06-19，覆盖 2 个合约。\n"
                "Open interest 集中合约：\n"
                "- SPY260619P00740000 put strike 740: open interest 5800, IV 0.19, Gamma 0.024"
            )
        }
    )

    result = tradingagents_state_to_result(
        execution_request,
        {
            "market_report": "市场报告显示价格高于均线，但短线动能减弱。",
            "fundamentals_report": "基本面报告提示估值和流动性需要继续观察。",
            "sentiment_report": "情绪报告显示风险偏好中性。",
            "news_report": "新闻报告提示宏观事件风险。",
            "investment_debate_state": {
                "bull_history": "多头情景关注趋势延续。",
                "bear_history": "空头情景关注波动率扩张。",
            },
        },
        "Overweight",
    )

    assert result.report.trade_plan != (
        "研究结论（原始 TradingAgents 输出）：\n"
        "Overweight\n\n"
        "仅用于研究复盘，不生成自动交易指令。"
    )
    assert "Overweight" in result.report.trade_plan
    assert "观察条件" in result.report.trade_plan
    assert "失效条件" in result.report.trade_plan
    assert "不生成自动交易指令" in result.report.trade_plan
    assert "后续 options-specific runner 中增强" not in result.report.options_observation
    for expected in ("IV", "偏斜", "open interest", "Gamma"):
        assert expected in result.report.options_observation
    assert "逐合约期权链快照" in result.report.options_observation
    assert "SPY260619P00740000" in result.report.options_observation


def test_real_tradingagents_mapped_report_passes_quality_contract(monkeypatch):
    monkeypatch.setattr(
        "app.analysis.tradingagents_runner.build_runner_verified_market_snapshot",
        lambda symbol, analysis_date: SNAPSHOT_FIXTURE,
    )
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

    assert report.evidence_labels == ["tradingagents-real-runner", "finance-data-hub-verified-snapshot"]
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
