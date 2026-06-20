from app.analysis.tradingagents_adapter import (
    TradingAgentsExecutionRequest,
    TradingAgentsReportPayload,
    TradingAgentsRunResult,
)
from app.analysis.schemas import AnalysisProgressEvent


def run_deterministic_research_fixture(
    execution_request: TradingAgentsExecutionRequest,
) -> TradingAgentsRunResult:
    if execution_request.symbol == "FAIL":
        raise RuntimeError("Deterministic TradingAgents fixture failure")

    symbol = execution_request.symbol
    report = TradingAgentsReportPayload(
        summary=f"{symbol} 中文 AI 投研摘要：本次 deterministic fixture 已通过 TradingAgents adapter 边界生成结构化研究报告。",
        market_background=f"{symbol} 研究背景聚焦美股市场、指数联动、流动性和关键宏观事件。",
        fundamental_analysis=f"{symbol} 基本面部分保留为研究框架输出，后续真实 runner 将接入 TradingAgents Agent 结论。",
        technical_analysis=f"{symbol} 技术面观察覆盖趋势、动量、成交量和关键价位结构。",
        sentiment_analysis=f"{symbol} 情绪面以新闻叙事、风险偏好和波动率变化作为后续真实执行输入。",
        options_observation=f"{symbol} 期权观察关注 IV、偏斜、成交量、open interest 和 gamma 风险。",
        bull_case=f"{symbol} 多头情景要求价格结构改善、风险偏好稳定且波动率不过度抬升。",
        bear_case=f"{symbol} 空头情景包括宏观冲击、波动率快速扩张或关键支撑失守。",
        risk_factors=["宏观事件", "波动率扩张", "流动性变化"],
        evidence_labels=["deterministic-tradingagents-fixture"],
        trade_plan="研究阶段仅输出观察计划，不生成自动交易指令。",
        position_sizing="研究阶段不生成实盘仓位。",
        take_profit_stop_loss="风控参考仅用于研究复盘，不代表交易执行建议。",
        confidence=0.61,
        markdown=(
            f"# {symbol} AI 投研报告\n\n"
            "## 摘要\n\n"
            f"{symbol} deterministic research fixture 已生成中文优先报告，用于验证分析执行和持久化链路。\n"
        ),
    )
    return TradingAgentsRunResult(
        progress=[
            AnalysisProgressEvent(step="queued", status="completed", message=f"{symbol} 分析任务已进入队列。"),
            AnalysisProgressEvent(step="market_data", status="completed", message="deterministic fixture 已准备研究输入。"),
            AnalysisProgressEvent(step="tradingagents", status="completed", message="TradingAgents adapter fixture 执行完成。"),
            AnalysisProgressEvent(step="report", status="completed", message="中文研究报告已生成并准备持久化。"),
        ],
        report=report,
    )
