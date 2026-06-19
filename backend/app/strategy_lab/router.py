from typing import Literal
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
from app.strategy_lab.catalog import (
    StrategyCatalogEntry,
    get_strategy_catalog_entry,
    list_strategy_catalog,
)

router = APIRouter(prefix="/api/strategy-lab", tags=["strategy-lab"])

ReviewStatus = Literal["draft", "reviewed", "candidate", "rejected"]


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


class StrategyCatalogItem(BaseModel):
    strategy_id: str
    name: str
    description: str
    scope: str
    default_parameters: dict
    parameter_schema: dict


class StrategyCatalogResponse(BaseModel):
    scope: str = "research_only"
    strategies: list[StrategyCatalogItem]


class StrategyExperimentCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=160)
    symbol: str = Field(min_length=1, max_length=64)
    strategy_id: str = Field(min_length=1, max_length=80)
    parameters: dict
    preview: dict
    tags: list[str] = Field(default_factory=list, max_length=12)
    notes: str | None = Field(default=None, max_length=2_000)
    report_id: UUID | None = None


class StrategyExperimentUpdateRequest(BaseModel):
    tags: list[str] | None = Field(default=None, max_length=12)
    notes: str | None = Field(default=None, max_length=2_000)
    archived: bool | None = None
    review_status: ReviewStatus | None = None
    review_checklist: dict | None = None


class StrategyExperimentResponse(BaseModel):
    experiment_id: UUID
    title: str
    symbol: str
    strategy_id: str
    scope: str
    parameters: dict
    preview: dict
    tags: list[str]
    notes: str | None = None
    archived: bool
    review_status: str
    review_checklist: dict
    report_id: UUID | None = None
    created_at: str
    updated_at: str


class StrategyExperimentListResponse(BaseModel):
    experiments: list[StrategyExperimentResponse]


class StrategyExperimentComparisonMetric(BaseModel):
    experiment_id: UUID
    title: str
    final_equity: float
    return_pct: float
    trade_count: int
    marker_count: int
    signal_count: int
    parameters: dict


class StrategyExperimentComparisonResponse(BaseModel):
    scope: str = "research_only"
    symbol: str
    base: StrategyExperimentComparisonMetric
    candidate: StrategyExperimentComparisonMetric
    deltas: dict
    parameter_deltas: dict


class StrategyExperimentCandidateItem(BaseModel):
    experiment_id: UUID
    title: str
    symbol: str
    strategy_id: str
    final_equity: float
    return_pct: float
    trade_count: int
    marker_count: int
    signal_count: int
    tags: list[str]
    review_checklist: dict
    created_at: str


class StrategyExperimentCandidateBoardResponse(BaseModel):
    scope: str = "research_only"
    candidates: list[StrategyExperimentCandidateItem]


@router.get("/strategies", response_model=StrategyCatalogResponse)
def list_strategies() -> StrategyCatalogResponse:
    return StrategyCatalogResponse(
        strategies=[to_catalog_item(entry) for entry in list_strategy_catalog()]
    )


@router.post("/signal-strategy/preview", response_model=SignalStrategyPreviewResponse)
def preview_signal_strategy(request: SignalStrategyPreviewRequest) -> SignalStrategyPreviewResponse:
    catalog_entry = get_strategy_catalog_entry(request.strategy_id)
    if catalog_entry is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="strategy not found")
    strategy = SignalStrategy(
        strategy_id=catalog_entry.strategy_id,
        name=catalog_entry.name,
        description=catalog_entry.description,
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


def to_catalog_item(entry: StrategyCatalogEntry) -> StrategyCatalogItem:
    return StrategyCatalogItem(
        strategy_id=entry.strategy_id,
        name=entry.name,
        description=entry.description,
        scope=entry.scope,
        default_parameters=entry.default_parameters,
        parameter_schema=entry.parameter_schema,
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
        tags=normalize_tags(request.tags),
        notes=request.notes,
        report_id=request.report_id,
    )
    session.add(experiment)
    session.commit()
    session.refresh(experiment)
    return to_experiment_response(experiment)


@router.get("/experiments", response_model=StrategyExperimentListResponse)
def list_strategy_experiments(
    symbol: str | None = None,
    tag: str | None = None,
    include_archived: bool = False,
    review_status: ReviewStatus | None = None,
    session: Session = Depends(get_db_session),
) -> StrategyExperimentListResponse:
    statement = select(StrategyExperimentModel).order_by(StrategyExperimentModel.created_at.desc())
    if symbol:
        statement = statement.where(StrategyExperimentModel.symbol == symbol.upper())
    if not include_archived:
        statement = statement.where(StrategyExperimentModel.archived.is_(False))
    if review_status:
        statement = statement.where(StrategyExperimentModel.review_status == review_status)
    experiments = session.scalars(statement.limit(100)).all()
    if tag:
        experiments = [
            experiment for experiment in experiments if tag.strip() in (experiment.tags or [])
        ]
    return StrategyExperimentListResponse(
        experiments=[to_experiment_response(experiment) for experiment in experiments[:50]]
    )


@router.get("/experiments/candidates", response_model=StrategyExperimentCandidateBoardResponse)
def list_strategy_experiment_candidates(
    symbol: str | None = None,
    strategy_id: str | None = None,
    tag: str | None = None,
    sort_by: Literal["created_at", "return_pct"] = "created_at",
    sort_order: Literal["asc", "desc"] = "desc",
    session: Session = Depends(get_db_session),
) -> StrategyExperimentCandidateBoardResponse:
    statement = select(StrategyExperimentModel).where(
        StrategyExperimentModel.review_status == "candidate",
        StrategyExperimentModel.archived.is_(False),
    )
    if symbol:
        statement = statement.where(StrategyExperimentModel.symbol == symbol.upper())
    if strategy_id:
        statement = statement.where(StrategyExperimentModel.strategy_id == strategy_id)

    experiments = session.scalars(statement.limit(100)).all()
    if tag:
        experiments = [
            experiment for experiment in experiments if tag.strip() in (experiment.tags or [])
        ]

    candidates = [to_candidate_item(experiment) for experiment in experiments]
    reverse = sort_order == "desc"
    if sort_by == "return_pct":
        candidates = sorted(candidates, key=lambda candidate: candidate.return_pct, reverse=reverse)
    else:
        candidates = sorted(candidates, key=lambda candidate: candidate.created_at, reverse=reverse)
    return StrategyExperimentCandidateBoardResponse(candidates=candidates[:50])


@router.get("/experiments/compare", response_model=StrategyExperimentComparisonResponse)
def compare_strategy_experiments(
    base_id: UUID,
    candidate_id: UUID,
    session: Session = Depends(get_db_session),
) -> StrategyExperimentComparisonResponse:
    base = session.get(StrategyExperimentModel, base_id)
    candidate = session.get(StrategyExperimentModel, candidate_id)
    if base is None or candidate is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="strategy experiment not found")
    if base.symbol != candidate.symbol:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="strategy experiments must share the same symbol",
        )

    base_metric = build_comparison_metric(base)
    candidate_metric = build_comparison_metric(candidate)
    return StrategyExperimentComparisonResponse(
        symbol=base.symbol,
        base=base_metric,
        candidate=candidate_metric,
        deltas={
            "final_equity": round(candidate_metric.final_equity - base_metric.final_equity, 6),
            "return_pct": round(candidate_metric.return_pct - base_metric.return_pct, 6),
            "trade_count": candidate_metric.trade_count - base_metric.trade_count,
            "marker_count": candidate_metric.marker_count - base_metric.marker_count,
            "signal_count": candidate_metric.signal_count - base_metric.signal_count,
        },
        parameter_deltas=build_parameter_deltas(base_metric.parameters, candidate_metric.parameters),
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


@router.patch("/experiments/{experiment_id}", response_model=StrategyExperimentResponse)
def update_strategy_experiment(
    experiment_id: UUID,
    request: StrategyExperimentUpdateRequest,
    session: Session = Depends(get_db_session),
) -> StrategyExperimentResponse:
    experiment = session.get(StrategyExperimentModel, experiment_id)
    if experiment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="strategy experiment not found")

    fields_set = request.model_fields_set
    if "tags" in fields_set:
        experiment.tags = normalize_tags(request.tags or [])
    if "notes" in fields_set:
        experiment.notes = request.notes
    if request.archived is not None:
        experiment.archived = request.archived
    if request.review_status is not None:
        experiment.review_status = request.review_status
    if "review_checklist" in fields_set:
        experiment.review_checklist = request.review_checklist or {}
    experiment.updated_at = utc_now_for_model()

    session.add(experiment)
    session.commit()
    session.refresh(experiment)
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
        tags=experiment.tags,
        notes=experiment.notes,
        archived=False,
        review_status="draft",
        review_checklist={},
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
        tags=experiment.tags or [],
        notes=experiment.notes,
        archived=experiment.archived,
        review_status=experiment.review_status,
        review_checklist=experiment.review_checklist or {},
        report_id=experiment.report_id,
        created_at=experiment.created_at.isoformat(),
        updated_at=experiment.updated_at.isoformat(),
    )


def to_candidate_item(experiment: StrategyExperimentModel) -> StrategyExperimentCandidateItem:
    metric = build_comparison_metric(experiment)
    return StrategyExperimentCandidateItem(
        experiment_id=experiment.id,
        title=experiment.title,
        symbol=experiment.symbol,
        strategy_id=experiment.strategy_id,
        final_equity=metric.final_equity,
        return_pct=metric.return_pct,
        trade_count=metric.trade_count,
        marker_count=metric.marker_count,
        signal_count=metric.signal_count,
        tags=experiment.tags or [],
        review_checklist=experiment.review_checklist or {},
        created_at=experiment.created_at.isoformat(),
    )


def normalize_tags(tags: list[str]) -> list[str]:
    normalized: list[str] = []
    for tag in tags:
        value = tag.strip()
        if value and value not in normalized:
            normalized.append(value)
    return normalized


def utc_now_for_model():
    from app.db.models import utc_now

    return utc_now()


def build_comparison_metric(experiment: StrategyExperimentModel) -> StrategyExperimentComparisonMetric:
    preview = experiment.preview_json
    backtest = preview.get("backtest", {})
    overlay = preview.get("overlay", {})
    signals = preview.get("signals", [])
    return StrategyExperimentComparisonMetric(
        experiment_id=experiment.id,
        title=experiment.title,
        final_equity=float(backtest.get("final_equity", 0)),
        return_pct=float(backtest.get("return_pct", 0)),
        trade_count=len(backtest.get("trades", [])),
        marker_count=len(overlay.get("markers", [])),
        signal_count=len(signals),
        parameters=experiment.parameters,
    )


def build_parameter_deltas(base_parameters: dict, candidate_parameters: dict) -> dict:
    parameter_keys = sorted(set(base_parameters) | set(candidate_parameters))
    return {
        key: {
            "base": base_parameters.get(key),
            "candidate": candidate_parameters.get(key),
            "changed": base_parameters.get(key) != candidate_parameters.get(key),
        }
        for key in parameter_keys
    }
