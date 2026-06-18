from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.strategy_lab.contracts import (
    SignalStrategy,
    build_chart_overlay,
    create_report_linked_note,
    run_deterministic_backtest,
)

router = APIRouter(prefix="/api/strategy-lab", tags=["strategy-lab"])


class SignalStrategyPreviewRequest(BaseModel):
    strategy_id: str = Field(default="ma-cross-research", min_length=1, max_length=80)
    name: str = Field(default="MA Cross Research", min_length=1, max_length=120)
    description: str = Field(default="Research-only moving average signal contract.", max_length=500)
    symbol: str = Field(default="SPY", min_length=1, max_length=64)
    fast_window: int = Field(default=2, ge=1, le=100)
    slow_window: int = Field(default=3, ge=1, le=200)
    initial_equity: float = Field(default=10_000, gt=0)
    bars: list[dict]
    report_id: str | None = None


class SignalStrategyPreviewResponse(BaseModel):
    strategy: dict
    signals: list[dict]
    backtest: dict
    overlay: dict
    note: dict | None = None
    scope: str = "research_only"


@router.post("/signal-strategy/preview", response_model=SignalStrategyPreviewResponse)
def preview_signal_strategy(request: SignalStrategyPreviewRequest) -> SignalStrategyPreviewResponse:
    strategy = SignalStrategy(
        strategy_id=request.strategy_id,
        name=request.name,
        description=request.description,
        parameters={
            "fast_window": request.fast_window,
            "slow_window": request.slow_window,
        },
    )
    signals = strategy.generate_signals(request.bars)
    backtest = run_deterministic_backtest(signals, initial_equity=request.initial_equity)
    overlay = build_chart_overlay(request.symbol.upper(), signals)
    note = None
    if request.report_id:
        note = create_report_linked_note(
            report_id=request.report_id,
            strategy_id=strategy.strategy_id,
            symbol=request.symbol.upper(),
            title=f"{strategy.name} research note",
            body="SignalStrategy preview generated from current research bars.",
            evidence_labels=["market-bars", "technical-setup"],
        )
    return SignalStrategyPreviewResponse(
        strategy={
            "strategy_id": strategy.strategy_id,
            "name": strategy.name,
            "description": strategy.description,
            "parameters": strategy.parameters,
        },
        signals=signals,
        backtest=backtest,
        overlay=overlay,
        note=note,
    )
