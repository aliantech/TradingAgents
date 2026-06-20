from datetime import date
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from app.analysis.schemas import AnalysisDepth, AnalysisRequest, AssetType, ReportLanguage, ResearchTemplate


EVALUATION_CASE_SET_VERSION = "phase-9-slice-2-v1"
DETERMINISTIC_PROVIDER = "deterministic-fixture"
DETERMINISTIC_MODEL = "tradingagents-local-fixture"


class EvaluationCaseCategory(StrEnum):
    spy_etf = "spy-etf"
    qqq_etf = "qqq-etf"
    mega_cap_equity = "mega-cap-equity"
    volatile_equity = "volatile-equity"
    index_oriented = "index-oriented"


class EvaluationExpectation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    required_evidence_labels: list[str] = Field(min_length=1)
    required_report_sections: list[str] = Field(min_length=1)
    required_safety_phrases: list[str] = Field(min_length=1)
    minimum_confidence: float = Field(ge=0, le=1)
    maximum_confidence: float = Field(ge=0, le=1)


class EvaluationCase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    case_id: str = Field(min_length=1, max_length=64)
    category: EvaluationCaseCategory
    symbol: str = Field(min_length=1, max_length=16)
    asset_type: AssetType
    analysis_date: date
    language: ReportLanguage = ReportLanguage.zh
    depth: AnalysisDepth
    analyst_set: str = Field(min_length=1, max_length=64)
    research_template: ResearchTemplate
    evaluation_focus: str = Field(min_length=1)
    expectation: EvaluationExpectation


class EvaluationCaseSet(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: str
    cases: list[EvaluationCase] = Field(min_length=1)


_DEFAULT_EXPECTATION = EvaluationExpectation(
    required_evidence_labels=["deterministic-tradingagents-fixture"],
    required_report_sections=[
        "summary",
        "market_background",
        "fundamental_analysis",
        "technical_analysis",
        "sentiment_analysis",
        "options_observation",
        "risk_factors",
    ],
    required_safety_phrases=["不生成自动交易指令", "不生成实盘仓位"],
    minimum_confidence=0.0,
    maximum_confidence=1.0,
)


EVALUATION_CASE_SET = EvaluationCaseSet(
    version=EVALUATION_CASE_SET_VERSION,
    cases=[
        EvaluationCase(
            case_id="spy-macro-options-2026-06-18",
            category=EvaluationCaseCategory.spy_etf,
            symbol="SPY",
            asset_type=AssetType.etf,
            analysis_date=date(2026, 6, 18),
            depth=AnalysisDepth.standard,
            analyst_set="macro-options",
            research_template=ResearchTemplate.macro_options_readthrough,
            evaluation_focus="Broad U.S. equity risk, liquidity, IV, and macro read-through.",
            expectation=_DEFAULT_EXPECTATION,
        ),
        EvaluationCase(
            case_id="qqq-technical-2026-06-18",
            category=EvaluationCaseCategory.qqq_etf,
            symbol="QQQ",
            asset_type=AssetType.etf,
            analysis_date=date(2026, 6, 18),
            depth=AnalysisDepth.standard,
            analyst_set="macro-options",
            research_template=ResearchTemplate.technical_setup,
            evaluation_focus="Growth-heavy ETF trend, momentum, breadth, and options risk.",
            expectation=_DEFAULT_EXPECTATION,
        ),
        EvaluationCase(
            case_id="aapl-mega-cap-2026-06-18",
            category=EvaluationCaseCategory.mega_cap_equity,
            symbol="AAPL",
            asset_type=AssetType.equity,
            analysis_date=date(2026, 6, 18),
            depth=AnalysisDepth.deep,
            analyst_set="macro-options",
            research_template=ResearchTemplate.general,
            evaluation_focus="Mega-cap single-name fundamentals, technical setup, and options relevance.",
            expectation=_DEFAULT_EXPECTATION,
        ),
        EvaluationCase(
            case_id="tsla-volatile-equity-2026-06-18",
            category=EvaluationCaseCategory.volatile_equity,
            symbol="TSLA",
            asset_type=AssetType.equity,
            analysis_date=date(2026, 6, 18),
            depth=AnalysisDepth.deep,
            analyst_set="macro-options",
            research_template=ResearchTemplate.technical_setup,
            evaluation_focus="High-volatility single-name narrative, IV risk, and risk-control clarity.",
            expectation=_DEFAULT_EXPECTATION,
        ),
        EvaluationCase(
            case_id="spx-index-readthrough-2026-06-18",
            category=EvaluationCaseCategory.index_oriented,
            symbol="SPX",
            asset_type=AssetType.index,
            analysis_date=date(2026, 6, 18),
            depth=AnalysisDepth.standard,
            analyst_set="macro-options",
            research_template=ResearchTemplate.macro_options_readthrough,
            evaluation_focus="Index-oriented market structure, macro risk, and options read-through.",
            expectation=_DEFAULT_EXPECTATION,
        ),
    ],
)


def list_evaluation_cases() -> list[EvaluationCase]:
    return list(EVALUATION_CASE_SET.cases)


def get_evaluation_case(case_id: str) -> EvaluationCase | None:
    return next((case for case in EVALUATION_CASE_SET.cases if case.case_id == case_id), None)


def build_analysis_request(case: EvaluationCase) -> AnalysisRequest:
    return AnalysisRequest(
        symbol=case.symbol,
        asset_type=case.asset_type,
        analysis_date=case.analysis_date,
        language=case.language,
        llm_provider=DETERMINISTIC_PROVIDER,
        model=DETERMINISTIC_MODEL,
        depth=case.depth,
        analyst_set=case.analyst_set,
        research_template=case.research_template,
    )


def validate_evaluation_case_set(case_set: EvaluationCaseSet = EVALUATION_CASE_SET) -> list[str]:
    errors: list[str] = []
    case_ids = [case.case_id for case in case_set.cases]
    symbols = {case.symbol for case in case_set.cases}
    categories = {case.category for case in case_set.cases}

    if len(case_ids) != len(set(case_ids)):
        errors.append("evaluation case ids must be unique")

    for symbol in ("SPY", "QQQ"):
        if symbol not in symbols:
            errors.append(f"evaluation case set must include {symbol}")

    for category in (
        EvaluationCaseCategory.mega_cap_equity,
        EvaluationCaseCategory.volatile_equity,
        EvaluationCaseCategory.index_oriented,
    ):
        if category not in categories:
            errors.append(f"evaluation case set must include {category.value}")

    for case in case_set.cases:
        if case.symbol != case.symbol.upper():
            errors.append(f"{case.case_id} symbol must be uppercase")
        if case.language != ReportLanguage.zh:
            errors.append(f"{case.case_id} must use Chinese-first report language")
        if case.expectation.minimum_confidence > case.expectation.maximum_confidence:
            errors.append(f"{case.case_id} has an invalid confidence range")

    return errors
