from app.reports.schemas import ResearchReport


def test_research_report_requires_chinese_sections():
    report = ResearchReport(
        analysis_id="00000000-0000-0000-0000-000000000001",
        symbol="SPY",
        language="zh",
        summary="SPY 当前趋势偏强，但需要关注波动率和宏观风险。",
        market_background="美股处于风险偏好修复阶段。",
        fundamental_analysis="ETF 本身不做公司基本面分析，重点观察成分股与估值。",
        technical_analysis="价格位于主要均线上方，MACD 维持正区间。",
        sentiment_analysis="新闻和市场情绪整体中性偏多。",
        options_observation="SPX/SPY 期权 IV 回落，0DTE 成交活跃。",
        bull_case="趋势延续和流动性改善支持上行。",
        bear_case="估值和事件风险可能触发回撤。",
        risk_factors=["FOMC", "VIX spike"],
        trade_plan="等待回踩关键均线后分批观察。",
        position_sizing="研究阶段不生成实盘仓位。",
        take_profit_stop_loss="以关键支撑和波动率变化作为风控参考。",
        confidence=0.62,
    )

    assert report.language == "zh"
    assert report.confidence == 0.62
    assert "SPX/SPY" in report.options_observation
