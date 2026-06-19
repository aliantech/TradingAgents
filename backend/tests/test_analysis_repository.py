from datetime import date
from uuid import uuid4

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.analysis.repository import AnalysisRepository
from app.analysis.schemas import AnalysisDepth, AnalysisProgressEvent, AnalysisRequest, AssetType, ReportLanguage
from app.analysis.store import AnalysisRun
from app.db.base import Base
from app.reports.schemas import ResearchReport


def _session():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def test_analysis_repository_persists_run_and_report():
    session = _session()
    repository = AnalysisRepository(session)
    analysis_id = uuid4()
    report_id = uuid4()
    request = AnalysisRequest(
        symbol="SPY",
        asset_type=AssetType.etf,
        analysis_date=date(2026, 6, 17),
        language=ReportLanguage.zh,
        llm_provider="openai",
        model="gpt-5.5",
        depth=AnalysisDepth.standard,
    )
    report = ResearchReport(
        report_id=report_id,
        analysis_id=analysis_id,
        symbol="SPY",
        language="zh",
        summary="SPY 中文摘要",
        market_background="市场背景",
        fundamental_analysis="基本面",
        technical_analysis="技术面",
        sentiment_analysis="情绪面",
        options_observation="期权观察",
        bull_case="多头",
        bear_case="空头",
        risk_factors=["FOMC"],
        trade_plan="研究计划",
        position_sizing="研究阶段不生成实盘仓位。",
        take_profit_stop_loss="风控参考",
        confidence=0.62,
        markdown="# SPY AI 投研报告",
    )
    run = AnalysisRun(
        analysis_id=analysis_id,
        request=request,
        status="completed",
        progress=[AnalysisProgressEvent(step="report", status="completed", message="persisted report fixture")],
        report=report,
    )

    repository.save_run(run)
    loaded = repository.get_run(analysis_id)

    assert loaded is not None
    assert loaded.analysis_id == analysis_id
    assert loaded.request.symbol == "SPY"
    assert loaded.progress[0].message == "persisted report fixture"
    assert loaded.report is not None
    assert loaded.report.report_id == report_id
    assert loaded.report.summary == "SPY 中文摘要"


def test_analysis_repository_lists_reports():
    session = _session()
    repository = AnalysisRepository(session)
    analysis_id = uuid4()
    report_id = uuid4()
    request = AnalysisRequest(
        symbol="SPY",
        asset_type=AssetType.etf,
        analysis_date=date(2026, 6, 17),
        language=ReportLanguage.zh,
        llm_provider="openai",
        model="gpt-5.5",
        depth=AnalysisDepth.standard,
    )
    report = ResearchReport(
        report_id=report_id,
        analysis_id=analysis_id,
        symbol="SPY",
        language="zh",
        summary="SPY 中文摘要",
        market_background="市场背景",
        fundamental_analysis="基本面",
        technical_analysis="技术面",
        sentiment_analysis="情绪面",
        options_observation="期权观察",
        bull_case="多头",
        bear_case="空头",
        risk_factors=["FOMC"],
        trade_plan="研究计划",
        position_sizing="研究阶段不生成实盘仓位。",
        take_profit_stop_loss="风控参考",
        confidence=0.62,
        markdown="# SPY AI 投研报告",
    )

    repository.save_run(AnalysisRun(analysis_id=analysis_id, request=request, status="completed", report=report))
    reports = repository.list_reports()

    assert len(reports) == 1
    assert reports[0].report_id == report_id
    assert reports[0].summary == "SPY 中文摘要"


def test_analysis_repository_hides_legacy_mock_reports():
    session = _session()
    repository = AnalysisRepository(session)
    analysis_id = uuid4()
    report_id = uuid4()
    request = AnalysisRequest(
        symbol="SPY",
        asset_type=AssetType.etf,
        analysis_date=date(2026, 6, 17),
        language=ReportLanguage.zh,
        llm_provider="openai",
        model="gpt-5.5",
        depth=AnalysisDepth.standard,
    )
    report = ResearchReport(
        report_id=report_id,
        analysis_id=analysis_id,
        symbol="SPY",
        language="zh",
        summary="SPY 当前趋势中性偏强，但需要结合 IV、成交量和宏观事件确认方向。",
        market_background="美股市场处于事件和流动性共同驱动阶段。",
        fundamental_analysis="第一阶段聚焦 ETF、指数和高流动性标的。",
        technical_analysis="价格结构以均线、成交量和动量指标为主。",
        sentiment_analysis="情绪分析优先聚合新闻和市场叙事，当前样例报告不接入实时社媒数据。",
        options_observation="期权观察重点包括 IV、delta、gamma、theta、vega、open interest。",
        bull_case="若价格站稳关键均线且 IV 未异常抬升，多头情景更有优势。",
        bear_case="若波动率快速上升、成交量背离或宏观事件冲击，需防范快速回撤。",
        risk_factors=["FOMC", "earnings risk", "VIX spike", "0DTE gamma risk"],
        evidence_labels=["market-bars", "options-chain", "provider-readiness", "tradingagents-debate"],
        trade_plan="第一阶段仅生成研究计划。",
        position_sizing="研究阶段不生成实盘仓位。",
        take_profit_stop_loss="风控参考。",
        confidence=0.62,
        markdown="# SPY AI 投研报告",
    )

    repository.save_run(AnalysisRun(analysis_id=analysis_id, request=request, status="completed", report=report))

    assert repository.list_reports() == []
    assert repository.get_report(report_id) is None
    assert repository.get_run(analysis_id).report is None


def test_analysis_repository_hides_phase_one_sample_reports():
    session = _session()
    repository = AnalysisRepository(session)
    analysis_id = uuid4()
    report_id = uuid4()
    request = AnalysisRequest(
        symbol="QQQ",
        asset_type=AssetType.etf,
        analysis_date=date(2026, 6, 17),
        language=ReportLanguage.zh,
        llm_provider="openai",
        model="gpt-5.5",
        depth=AnalysisDepth.standard,
    )
    report = ResearchReport(
        report_id=report_id,
        analysis_id=analysis_id,
        symbol="QQQ",
        language="zh",
        summary="QQQ sample report",
        market_background="sample",
        fundamental_analysis="sample",
        technical_analysis="sample",
        sentiment_analysis="新闻与市场情绪暂按中性处理，等待外部新闻源接入后增强。",
        options_observation="sample",
        bull_case="sample",
        bear_case="sample",
        risk_factors=[],
        evidence_labels=["AQuantLens Phase 1 sample report"],
        trade_plan="sample",
        position_sizing="sample",
        take_profit_stop_loss="sample",
        confidence=0.5,
        markdown="# QQQ\n\nAQuantLens Phase 1 sample report",
    )

    repository.save_run(AnalysisRun(analysis_id=analysis_id, request=request, status="completed", report=report))

    assert repository.list_reports() == []
    assert repository.get_report(report_id) is None
    assert repository.get_run(analysis_id).report is None
