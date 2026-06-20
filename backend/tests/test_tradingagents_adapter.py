from datetime import date
from uuid import uuid4

from app.analysis.schemas import AnalysisDepth, AnalysisRequest, AssetType, ReportLanguage, ResearchTemplate
from app.analysis.tradingagents_adapter import (
    TradingAgentsReportPayload,
    TradingAgentsRunResult,
    build_tradingagents_request,
    map_tradingagents_error,
    tradingagents_result_to_report,
)


def test_tradingagents_adapter_maps_analysis_request_to_execution_contract():
    analysis_id = uuid4()
    request = analysis_request(symbol="spy", depth=AnalysisDepth.deep, research_template=ResearchTemplate.technical_setup)

    execution_request = build_tradingagents_request(analysis_id, request)

    assert execution_request.analysis_id == analysis_id
    assert execution_request.symbol == "SPY"
    assert execution_request.asset_type == "etf"
    assert execution_request.analysis_date == date(2026, 6, 20)
    assert execution_request.language == "zh"
    assert execution_request.llm_provider == "openai"
    assert execution_request.model == "gpt-5.5"
    assert execution_request.depth == "deep"
    assert execution_request.analyst_set == "macro-options"
    assert execution_request.research_template == "technical-setup"
    assert execution_request.runtime_config == {
        "symbol": "SPY",
        "date": "2026-06-20",
        "llm_provider": "openai",
        "model": "gpt-5.5",
        "depth": "deep",
        "analyst_set": "macro-options",
        "research_template": "technical-setup",
    }


def test_tradingagents_adapter_maps_result_to_existing_report_schema():
    analysis_id = uuid4()
    report_id = uuid4()
    execution_request = build_tradingagents_request(analysis_id, analysis_request())
    result = TradingAgentsRunResult(
        progress=[
            {"step": "market_data", "status": "completed", "message": "Market data loaded."},
            {"step": "report", "status": "completed", "message": "Research report generated."},
        ],
        report=TradingAgentsReportPayload(
            summary="SPY 中文研究摘要",
            market_background="市场背景",
            fundamental_analysis="基本面",
            technical_analysis="技术面",
            sentiment_analysis="情绪面",
            options_observation="期权观察",
            bull_case="多头情景",
            bear_case="空头情景",
            risk_factors=["FOMC", "IV spike"],
            evidence_labels=["tradingagents-research"],
            trade_plan="研究计划",
            position_sizing="研究阶段不生成实盘仓位。",
            take_profit_stop_loss="风控参考",
            confidence=0.68,
            markdown="# SPY AI 投研报告",
        ),
    )

    report = tradingagents_result_to_report(
        execution_request=execution_request,
        result=result,
        report_id=report_id,
    )

    assert report.analysis_id == analysis_id
    assert report.report_id == report_id
    assert report.symbol == "SPY"
    assert report.language == "zh"
    assert report.analyst_set == "macro-options"
    assert report.research_template == "general"
    assert report.summary == "SPY 中文研究摘要"
    assert report.confidence == 0.68
    assert report.evidence_labels == ["tradingagents-research"]


def test_tradingagents_adapter_sanitizes_provider_errors_for_progress_events():
    event = map_tradingagents_error(
        RuntimeError("OpenAI failed with api_key=sk-secret-123 Bearer abc.def token=my-token password=hunter2")
    )

    assert event.step == "tradingagents"
    assert event.status == "failed"
    assert "sk-secret" not in event.message
    assert "Bearer abc.def" not in event.message
    assert "my-token" not in event.message
    assert "hunter2" not in event.message
    assert "[redacted]" in event.message


def test_tradingagents_adapter_does_not_expose_broker_or_live_execution_surface():
    import app.analysis.tradingagents_adapter as adapter

    public_names = " ".join(name.lower() for name in dir(adapter) if not name.startswith("_"))
    assert "broker" not in public_names
    assert "live" not in public_names
    assert "credential" not in public_names
    assert "place_order" not in public_names
    assert "submit_order" not in public_names


def analysis_request(
    *,
    symbol="SPY",
    depth=AnalysisDepth.standard,
    research_template=ResearchTemplate.general,
):
    return AnalysisRequest(
        symbol=symbol,
        asset_type=AssetType.etf,
        analysis_date=date(2026, 6, 20),
        language=ReportLanguage.zh,
        llm_provider="openai",
        model="gpt-5.5",
        depth=depth,
        analyst_set="macro-options",
        research_template=research_template,
    )
