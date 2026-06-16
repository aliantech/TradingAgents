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
        progress=[AnalysisProgressEvent(step="report", status="completed", message="中文结构化报告已生成。")],
        report=report,
    )

    repository.save_run(run)
    loaded = repository.get_run(analysis_id)

    assert loaded is not None
    assert loaded.analysis_id == analysis_id
    assert loaded.request.symbol == "SPY"
    assert loaded.progress[0].message == "中文结构化报告已生成。"
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
