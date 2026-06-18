from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import StrategyExperimentModel
from app.db.session import get_db_session

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


class StrategyExperimentCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=160)
    symbol: str = Field(min_length=1, max_length=64)
    strategy_id: str = Field(min_length=1, max_length=80)
    parameters: dict
    preview: dict
    report_id: UUID | None = None


class StrategyExperimentResponse(BaseModel):
    experiment_id: UUID
    title: str
    symbol: str
    strategy_id: str
    scope: str
    parameters: dict
    preview: dict
    report_id: UUID | None = None
    created_at: str
    updated_at: str


class StrategyExperimentListResponse(BaseModel):
    experiments: list[StrategyExperimentResponse]


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


@router.post(
    "/experiments",
    response_model=StrategyExperimentResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_strategy_experiment(
    request: StrategyExperimentCreateRequest,
    session: Session = Depends(get_db_session),
) -> StrategyExperimentResponse:
    experiment = StrategyExperimentModel(
        title=request.title,
        symbol=request.symbol.upper(),
        strategy_id=request.strategy_id,
        scope="research_only",
        parameters=request.parameters,
        preview_json=request.preview,
        report_id=request.report_id,
    )
    session.add(experiment)
    session.commit()
    session.refresh(experiment)
    return to_experiment_response(experiment)


@router.get("/experiments", response_model=StrategyExperimentListResponse)
def list_strategy_experiments(
    symbol: str | None = None,
    session: Session = Depends(get_db_session),
) -> StrategyExperimentListResponse:
    statement = select(StrategyExperimentModel).order_by(StrategyExperimentModel.created_at.desc())
    if symbol:
        statement = statement.where(StrategyExperimentModel.symbol == symbol.upper())
    experiments = session.scalars(statement.limit(50)).all()
    return StrategyExperimentListResponse(
        experiments=[to_experiment_response(experiment) for experiment in experiments]
    )


@router.get("/experiments/{experiment_id}", response_model=StrategyExperimentResponse)
def get_strategy_experiment(
    experiment_id: UUID,
    session: Session = Depends(get_db_session),
) -> StrategyExperimentResponse:
    experiment = session.get(StrategyExperimentModel, experiment_id)
    if experiment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="strategy experiment not found")
    return to_experiment_response(experiment)


@router.post(
    "/experiments/{experiment_id}/duplicate",
    response_model=StrategyExperimentResponse,
    status_code=status.HTTP_201_CREATED,
)
def duplicate_strategy_experiment(
    experiment_id: UUID,
    session: Session = Depends(get_db_session),
) -> StrategyExperimentResponse:
    experiment = session.get(StrategyExperimentModel, experiment_id)
    if experiment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="strategy experiment not found")
    duplicated = StrategyExperimentModel(
        title=f"{experiment.title} Copy",
        symbol=experiment.symbol,
        strategy_id=experiment.strategy_id,
        scope=experiment.scope,
        parameters=experiment.parameters,
        preview_json=experiment.preview_json,
        report_id=experiment.report_id,
    )
    session.add(duplicated)
    session.commit()
    session.refresh(duplicated)
    return to_experiment_response(duplicated)


def to_experiment_response(experiment: StrategyExperimentModel) -> StrategyExperimentResponse:
    return StrategyExperimentResponse(
        experiment_id=experiment.id,
        title=experiment.title,
        symbol=experiment.symbol,
        strategy_id=experiment.strategy_id,
        scope=experiment.scope,
        parameters=experiment.parameters,
        preview=experiment.preview_json,
        report_id=experiment.report_id,
        created_at=experiment.created_at.isoformat(),
        updated_at=experiment.updated_at.isoformat(),
    )
