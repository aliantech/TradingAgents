from datetime import date
from uuid import UUID, uuid4

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.analysis.repository import AnalysisRepository
from app.analysis.schemas import AnalysisDepth, AnalysisRequest, AssetType, ReportLanguage
from app.analysis.store import AnalysisRun, analysis_store
from app.db.base import Base
from app.main import app
from app.reports.schemas import ReportReviewCreate, ResearchReport


def _session():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def test_report_review_repository_creates_and_lists_reviews():
    session = _session()
    repository = AnalysisRepository(session)
    report_id = _save_report(repository)

    created = repository.create_report_review(
        report_id,
        ReportReviewCreate(
            reviewer="operator-a",
            evidence_clarity=4,
            consistency=5,
            risk_coverage=4,
            options_relevance=3,
            chinese_readability=5,
            research_only_safety=5,
            notes="证据链清楚，期权部分还可以继续增强。",
        ),
    )
    reviews = repository.list_report_reviews(report_id)

    assert created is not None
    assert created.report_id == report_id
    assert created.reviewer == "operator-a"
    assert created.research_only_safety == 5
    assert reviews == [created]


def test_report_review_repository_returns_none_for_missing_report():
    session = _session()
    repository = AnalysisRepository(session)

    assert repository.create_report_review(uuid4(), _review_payload()) is None
    assert repository.list_report_reviews(uuid4()) is None


def test_report_review_api_creates_and_lists_reviews_for_completed_report():
    client = TestClient(app)
    report_id = _create_completed_report(client, "RVWAPI")

    create_response = client.post(
        f"/api/reports/{report_id}/reviews",
        json={
            "reviewer": "operator-a",
            "evidence_clarity": 4,
            "consistency": 4,
            "risk_coverage": 5,
            "options_relevance": 3,
            "chinese_readability": 5,
            "research_only_safety": 5,
            "notes": "结构清楚，保留研究边界。",
        },
    )
    list_response = client.get(f"/api/reports/{report_id}/reviews")
    reports_response = client.get("/api/reports")

    assert create_response.status_code == 201
    created = create_response.json()
    assert created["report_id"] == report_id
    assert created["reviewer"] == "operator-a"
    assert created["research_only_safety"] == 5
    assert created["notes"] == "结构清楚，保留研究边界。"

    assert list_response.status_code == 200
    assert list_response.json()[0]["review_id"] == created["review_id"]
    assert reports_response.status_code == 200
    assert any(report["report_id"] == report_id for report in reports_response.json())


def test_report_review_api_rejects_invalid_score_and_missing_report():
    client = TestClient(app)

    missing_response = client.post(f"/api/reports/{uuid4()}/reviews", json=_review_payload().model_dump())
    invalid_score_response = client.post(
        f"/api/reports/{uuid4()}/reviews",
        json={**_review_payload().model_dump(), "evidence_clarity": 6},
    )

    assert missing_response.status_code == 404
    assert invalid_score_response.status_code == 422


def _save_report(repository: AnalysisRepository) -> UUID:
    analysis_id = uuid4()
    report_id = uuid4()
    request = AnalysisRequest(
        symbol="SPY",
        asset_type=AssetType.etf,
        analysis_date=date(2026, 6, 18),
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
    return report_id


def _create_completed_report(client: TestClient, symbol: str) -> str:
    response = client.post(
        "/api/analysis",
        json={
            "symbol": symbol,
            "asset_type": "equity",
            "analysis_date": "2026-06-18",
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
    return status_response.json()["report_id"]


def _review_payload() -> ReportReviewCreate:
    return ReportReviewCreate(
        reviewer="operator-a",
        evidence_clarity=4,
        consistency=4,
        risk_coverage=4,
        options_relevance=4,
        chinese_readability=5,
        research_only_safety=5,
        notes="研究评审记录。",
    )
