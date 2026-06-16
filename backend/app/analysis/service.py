from uuid import UUID, uuid4

from app.analysis.schemas import AnalysisProgressEvent, AnalysisRequest
from app.analysis.store import AnalysisRun, analysis_store
from app.reports.schemas import ResearchReport


def _build_progress(symbol: str) -> list[AnalysisProgressEvent]:
    return [
        AnalysisProgressEvent(step="queued", status="completed", message=f"{symbol} 分析任务已进入队列。"),
        AnalysisProgressEvent(step="market_data", status="completed", message="已加载基础行情、K 线和期权上下文。"),
        AnalysisProgressEvent(step="agents", status="completed", message="分析师、研究员和风控角色已完成第一轮研究。"),
        AnalysisProgressEvent(step="report", status="completed", message="中文结构化报告已生成。"),
    ]


def _build_report(analysis_id: UUID, report_id: UUID, request: AnalysisRequest) -> ResearchReport:
    symbol = request.symbol.upper()
    markdown = "\n".join(
        [
            f"# {symbol} AI 投研报告",
            "",
            "## 摘要",
            f"{symbol} 当前适合进入研究跟踪状态，短期需要同时观察价格趋势、波动率和期权成交结构。",
            "",
            "## 风险提示",
            "本报告仅用于研究，不构成投资建议，也不会触发实盘下单。",
        ]
    )
    return ResearchReport(
        report_id=report_id,
        analysis_id=analysis_id,
        symbol=symbol,
        language=request.language,
        summary=f"{symbol} 当前趋势中性偏强，但需要结合 IV、成交量和宏观事件确认方向。",
        market_background="美股市场处于事件和流动性共同驱动阶段，指数波动可能受利率、财报和风险偏好影响。",
        fundamental_analysis="第一阶段聚焦 ETF、指数和高流动性标的，基本面部分先使用成分股、估值和宏观背景做研究注释。",
        technical_analysis="价格结构以均线、成交量和动量指标为主，后续将接入 MA/EMA/MACD/RSI/BOLL 等可验证指标。",
        sentiment_analysis="情绪分析优先聚合新闻和市场叙事，当前样例报告不接入实时社媒数据。",
        options_observation="期权观察重点包括 IV、delta、gamma、theta、vega、open interest、0DTE 活跃度和 ATM 附近成交。",
        bull_case="若价格站稳关键均线且 IV 未异常抬升，多头情景更有优势。",
        bear_case="若波动率快速上升、成交量背离或宏观事件冲击，需防范快速回撤。",
        risk_factors=["FOMC", "earnings risk", "VIX spike", "0DTE gamma risk"],
        trade_plan="第一阶段仅生成研究计划：等待关键价位确认后再进入策略评估，不直接生成实盘订单。",
        position_sizing="研究阶段不生成实盘仓位；后续必须经过 risk engine 和 paper trading 验证。",
        take_profit_stop_loss="以关键支撑/阻力、IV 变化和最大可承受亏损作为止盈止损研究参考。",
        confidence=0.62,
        markdown=markdown,
    )


def start_analysis(request: AnalysisRequest) -> AnalysisRun:
    analysis_id = uuid4()
    report_id = uuid4()
    normalized_request = request.model_copy(update={"symbol": request.symbol.upper()})
    run = AnalysisRun(
        analysis_id=analysis_id,
        request=normalized_request,
        status="completed",
        progress=_build_progress(normalized_request.symbol),
    )
    run.report = _build_report(analysis_id, report_id, normalized_request)
    return analysis_store.save(run)
