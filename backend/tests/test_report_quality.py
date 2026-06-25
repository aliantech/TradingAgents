import pytest

from app.reports.quality import ReportQualityError, research_report_quality_issues, validate_research_report_quality
from app.reports.schemas import ResearchReport


def test_valid_chinese_research_report_passes_quality_contract():
    report = quality_report()

    validate_research_report_quality(report)

    assert research_report_quality_issues(report) == []


def test_quality_contract_requires_chinese_first_sections():
    report = quality_report(market_background="US market background without Chinese text.")

    issues = research_report_quality_issues(report)

    assert any(issue.field == "market_background" for issue in issues)


def test_quality_contract_requires_evidence_labels():
    report = quality_report(evidence_labels=[])

    with pytest.raises(ReportQualityError, match="evidence_labels"):
        validate_research_report_quality(report)


def test_quality_contract_requires_research_only_language():
    report = quality_report(
        trade_plan="立即买入。",
        position_sizing="满仓。",
        take_profit_stop_loss="止盈止损。",
    )

    with pytest.raises(ReportQualityError, match="trade_authority"):
        validate_research_report_quality(report)


def test_quality_contract_rejects_real_runner_close_conflict_with_verified_snapshot():
    report = quality_report(
        evidence_labels=["tradingagents-real-runner", "direct-yahoo-chart-verified-snapshot"],
        markdown=(
            "## Verified market data snapshot for SPY\n\n"
            "- Latest trading row used: 2026-06-18\n\n"
            "### Latest verified OHLCV row\n\n"
            "| Field | Value |\n"
            "|---|---:|\n"
            "| Close | 549.33 |\n\n"
            "## 市场分析\n\n"
            "模型报告称 2026-06-18 的 Close 为 746.74。"
        ),
    )

    with pytest.raises(ReportQualityError, match="market_data_grounding"):
        validate_research_report_quality(report)


def quality_report(**overrides):
    values = {
        "analysis_id": "00000000-0000-0000-0000-000000000001",
        "symbol": "SPY",
        "language": "zh",
        "summary": "SPY 中文 AI 投研摘要，聚焦市场、波动率和风险边界。",
        "market_background": "美股风险偏好修复，但宏观事件仍会影响指数波动。",
        "fundamental_analysis": "ETF 研究重点观察成分股盈利、估值和流动性。",
        "technical_analysis": "价格位于关键均线上方，趋势仍需成交量确认。",
        "sentiment_analysis": "新闻和市场情绪中性偏多，仍需观察风险事件。",
        "options_observation": "期权 IV 回落，偏斜和 gamma 暴露需要继续跟踪。",
        "bull_case": "多头情景依赖流动性改善和风险偏好延续。",
        "bear_case": "空头情景包括宏观冲击、波动率抬升和关键支撑失守。",
        "risk_factors": ["宏观事件", "波动率扩张"],
        "evidence_labels": ["deterministic-tradingagents-fixture"],
        "trade_plan": "研究阶段仅输出观察计划，不生成自动交易指令。",
        "position_sizing": "研究阶段不生成实盘仓位。",
        "take_profit_stop_loss": "风控参考仅用于研究复盘，不代表交易执行建议。",
        "confidence": 0.61,
    }
    values.update(overrides)
    return ResearchReport(**values)
