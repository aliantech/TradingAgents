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
            "tool_vendors": {
                **config.get("tool_vendors", {}),
                "get_macro_indicators": "macro_unavailable",
                "get_indicators": "direct_yahoo_chart",
                "get_stock_data": "direct_yahoo_chart",
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
    market_report = str(final_state.get("market_report") or "未返回市场分析。")
    fundamentals_report = str(final_state.get("fundamentals_report") or "未返回基本面分析。")
    sentiment_report = str(final_state.get("sentiment_report") or "未返回情绪分析。")
    news_report = str(final_state.get("news_report") or "未返回新闻分析。")
    debate = final_state.get("investment_debate_state") or {}
    bull_case = str(debate.get("bull_history") or "未返回多头辩论。")
    bear_case = str(debate.get("bear_history") or "未返回空头辩论。")
    final_decision = str(decision or final_state.get("final_trade_decision") or "未返回最终研究结论。")

    report = TradingAgentsReportPayload(
        summary=f"{symbol} 中文 AI 投研摘要：真实 TradingAgents runner 已完成研究执行。",
        market_background=market_report,
        fundamental_analysis=fundamentals_report,
        technical_analysis=market_report,
        sentiment_analysis=f"{sentiment_report}\n\n{news_report}",
        options_observation="真实 TradingAgents runner 当前主要返回股票研究状态；期权观察将在后续 options-specific runner 中增强。",
        bull_case=bull_case,
        bear_case=bear_case,
        risk_factors=["模型输出不确定性", "数据源可用性", "宏观事件"],
        evidence_labels=["tradingagents-real-runner"],
        trade_plan=final_decision,
        position_sizing="研究阶段不生成实盘仓位。",
        take_profit_stop_loss="风控参考仅用于研究复盘，不代表交易执行建议。",
        confidence=0.5,
        markdown=build_real_runner_markdown(
            symbol=symbol,
            market_report=market_report,
            fundamentals_report=fundamentals_report,
            sentiment_report=sentiment_report,
            news_report=news_report,
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


def build_real_runner_markdown(
    *,
    symbol: str,
    market_report: str,
    fundamentals_report: str,
    sentiment_report: str,
    news_report: str,
    final_decision: str,
) -> str:
    return (
        f"# {symbol} AI 投研报告\n\n"
        "## 市场分析\n\n"
        f"{market_report}\n\n"
        "## 基本面\n\n"
        f"{fundamentals_report}\n\n"
        "## 情绪与新闻\n\n"
        f"{sentiment_report}\n\n{news_report}\n\n"
        "## 研究结论\n\n"
        f"{final_decision}\n"
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
