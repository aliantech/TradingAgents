from copy import deepcopy
from pathlib import Path
import sys
from typing import Any

from app.analysis.deterministic_runner import run_deterministic_research_fixture
from app.analysis.schemas import AnalysisProgressEvent
from app.analysis.tradingagents_adapter import (
    TradingAgentsExecutionRequest,
    TradingAgentsReportPayload,
    TradingAgentsRunResult,
)
from app.core.config import Settings

REAL_TRADINGAGENTS_MODE = "real-tradingagents"


def run_configured_research(
    execution_request: TradingAgentsExecutionRequest,
    runtime_settings: Settings,
) -> TradingAgentsRunResult:
    if runtime_settings.tradingagents_runner_mode == REAL_TRADINGAGENTS_MODE:
        return run_real_tradingagents_research(execution_request, runtime_settings)
    return run_deterministic_research_fixture(execution_request)


def run_real_tradingagents_research(
    execution_request: TradingAgentsExecutionRequest,
    runtime_settings: Settings,
) -> TradingAgentsRunResult:
    if runtime_settings.tradingagents_runner_mode != REAL_TRADINGAGENTS_MODE:
        raise RuntimeError("Real TradingAgents runner is disabled by runtime settings.")

    ensure_tradingagents_import_path()
    from tradingagents.graph import TradingAgentsGraph

    config = build_real_tradingagents_config(execution_request, runtime_settings)
    graph = TradingAgentsGraph(
        selected_analysts=parse_selected_analysts(runtime_settings.tradingagents_selected_analysts),
        config=config,
    )
    final_state, decision = graph.propagate(
        execution_request.symbol,
        execution_request.analysis_date,
        asset_type=tradingagents_asset_type(execution_request.asset_type),
    )
    return tradingagents_state_to_result(execution_request, final_state, decision)


def build_real_tradingagents_config(
    execution_request: TradingAgentsExecutionRequest,
    runtime_settings: Settings,
) -> dict[str, Any]:
    ensure_tradingagents_import_path()
    from tradingagents.default_config import DEFAULT_CONFIG

    config = deepcopy(DEFAULT_CONFIG)
    config.update(
        {
            "llm_provider": runtime_settings.tradingagents_llm_provider or execution_request.llm_provider,
            "deep_think_llm": runtime_settings.tradingagents_deep_think_llm or execution_request.model,
            "quick_think_llm": runtime_settings.tradingagents_quick_think_llm or execution_request.model,
            "output_language": runtime_settings.tradingagents_output_language,
            "max_debate_rounds": runtime_settings.tradingagents_max_debate_rounds,
            "max_risk_discuss_rounds": runtime_settings.tradingagents_max_risk_discuss_rounds,
            "checkpoint_enabled": False,
            "finance_data_hub_base_url": runtime_settings.finance_data_hub_base_url,
            "tool_vendors": {
                **config.get("tool_vendors", {}),
                "get_macro_indicators": "macro_unavailable",
                "get_indicators": "finance_data_hub",
                "get_stock_data": "finance_data_hub",
            },
        }
    )
    return config


def tradingagents_state_to_result(
    execution_request: TradingAgentsExecutionRequest,
    final_state: dict[str, Any],
    decision: str,
) -> TradingAgentsRunResult:
    symbol = execution_request.symbol
    verified_snapshot = build_runner_verified_market_snapshot(symbol, execution_request.analysis_date.isoformat())
    market_report = str(final_state.get("market_report") or "未返回市场分析。")
    fundamentals_report = str(final_state.get("fundamentals_report") or "未返回基本面分析。")
    sentiment_report = str(final_state.get("sentiment_report") or "未返回情绪分析。")
    news_report = str(final_state.get("news_report") or "未返回新闻分析。")
    debate = final_state.get("investment_debate_state") or {}
    bull_case = str(debate.get("bull_history") or "未返回多头辩论。")
    bear_case = str(debate.get("bear_history") or "未返回空头辩论。")
    final_decision = str(decision or final_state.get("final_trade_decision") or "未返回最终研究结论。")

    grounded_market_report = build_grounded_market_report(verified_snapshot, market_report)
    options_observation = build_real_runner_options_observation(symbol, execution_request.option_chain_context)
    trade_plan = build_real_runner_trade_plan(final_decision)

    report = TradingAgentsReportPayload(
        summary=f"{symbol} 中文 AI 投研摘要：真实 TradingAgents runner 已完成研究执行。",
        market_background=grounded_market_report,
        fundamental_analysis=fundamentals_report,
        technical_analysis=grounded_market_report,
        sentiment_analysis=f"{sentiment_report}\n\n{news_report}",
        options_observation=options_observation,
        bull_case=bull_case,
        bear_case=bear_case,
        risk_factors=["模型输出不确定性", "数据源可用性", "宏观事件"],
        evidence_labels=["tradingagents-real-runner", "finance-data-hub-verified-snapshot"],
        trade_plan=trade_plan,
        position_sizing="研究阶段不生成实盘仓位。",
        take_profit_stop_loss="风控参考仅用于研究复盘，不代表交易执行建议。",
        confidence=0.5,
        markdown=build_real_runner_markdown(
            symbol=symbol,
            verified_snapshot=verified_snapshot,
            market_report=market_report,
            fundamentals_report=fundamentals_report,
            sentiment_report=sentiment_report,
            news_report=news_report,
            options_observation=options_observation,
            trade_plan=trade_plan,
            final_decision=final_decision,
        ),
    )
    return TradingAgentsRunResult(
        progress=[
            AnalysisProgressEvent(step="queued", status="completed", message=f"{symbol} 分析任务已进入队列。"),
            AnalysisProgressEvent(step="tradingagents", status="completed", message="真实 TradingAgents runner 执行完成。"),
            AnalysisProgressEvent(step="report", status="completed", message="真实 TradingAgents 输出已映射为中文研究报告。"),
        ],
        report=report,
    )


def build_grounded_market_report(verified_snapshot: str, market_report: str) -> str:
    return (
        "数据校验快照（精确价格、OHLCV 和技术指标以此为准）：\n"
        f"{verified_snapshot}\n\n"
        "TradingAgents 市场分析原文（如与上方快照冲突，以上方快照为准）：\n"
        f"{market_report}"
    )


def build_runner_verified_market_snapshot(symbol: str, analysis_date: str) -> str:
    ensure_tradingagents_import_path()
    from tradingagents.dataflows.market_data_validator import build_verified_market_snapshot

    return build_verified_market_snapshot(symbol, analysis_date)


def build_real_runner_options_observation(symbol: str, option_chain_context: str = "") -> str:
    base_observation = (
        f"{symbol} 期权观察应作为风险读数而不是交易指令：重点跟踪 IV 水平与期限结构、put/call 偏斜、"
        "open interest 和成交量是否集中在关键执行价、Gamma 暴露是否放大盘中波动，以及事件日前后隐含波动率"
        "回落风险。"
    )
    if option_chain_context.strip():
        return (
            f"{base_observation}\n\n"
            f"{option_chain_context.strip()}\n\n"
            "上述逐合约快照来自已持久化期权链数据，只用于人工复核 IV、open interest 和 Gamma 风险，"
            "不生成期权买卖建议。"
        )
    return (
        f"{base_observation}当前未找到可用的逐合约期权链快照，因此本节只给出需要人工复核的期权"
        "风险框架，不生成期权买卖建议。"
    )


def build_real_runner_trade_plan(final_decision: str) -> str:
    decision = final_decision.strip() or "未返回最终研究结论。"
    return (
        "研究计划（由真实 TradingAgents 最终结论映射）：\n"
        f"- 原始 TradingAgents 结论：{decision}\n"
        "- 观察条件：仅在已验证市场快照、市场分析、基本面叙事、情绪新闻和风险情景彼此一致时，才把该结论作为研究假设继续跟踪。\n"
        "- 失效条件：若价格与已验证快照冲突、宏观/新闻风险显著改变、波动率快速扩张，或多空辩论出现新的核心反证，应将该结论降级为待复核。\n"
        "- 风险边界：本系统当前仅用于研究复盘和人工复核线索，不计算实盘仓位，不发送订单，也不生成自动交易指令。\n"
        "- 后续复核：下一轮应补充期权链、IV、偏斜、open interest、Gamma 暴露和事件风险后，再评估是否具备更高置信度。"
    )


def build_real_runner_markdown(
    *,
    symbol: str,
    verified_snapshot: str,
    market_report: str,
    fundamentals_report: str,
    sentiment_report: str,
    news_report: str,
    options_observation: str,
    trade_plan: str,
    final_decision: str,
) -> str:
    return (
        f"# {symbol} AI 投研报告\n\n"
        "## 数据校验快照\n\n"
        f"{verified_snapshot}\n\n"
        "## 市场分析\n\n"
        f"{market_report}\n\n"
        "## 基本面\n\n"
        f"{fundamentals_report}\n\n"
        "## 情绪与新闻\n\n"
        f"{sentiment_report}\n\n{news_report}\n\n"
        "## 期权观察\n\n"
        f"{options_observation}\n\n"
        "## 研究结论\n\n"
        f"{final_decision}\n\n"
        "## 研究计划\n\n"
        f"{trade_plan}\n"
    )


def parse_selected_analysts(value: str) -> list[str]:
    analysts = [item.strip() for item in value.split(",") if item.strip()]
    return analysts or ["market", "news", "fundamentals"]


def tradingagents_asset_type(asset_type: str) -> str:
    if asset_type == "crypto":
        return "crypto"
    return "stock"


def ensure_tradingagents_import_path() -> None:
    repo_root = Path(__file__).resolve().parents[3]
    repo_root_text = str(repo_root)
    if repo_root_text not in sys.path:
        sys.path.insert(0, repo_root_text)
