from app.analysis.schemas import AssetType, ReportLanguage
from app.research_evaluation.cases import (
    DETERMINISTIC_MODEL,
    DETERMINISTIC_PROVIDER,
    EVALUATION_CASE_SET_VERSION,
    build_analysis_request,
    get_evaluation_case,
    list_evaluation_cases,
    validate_evaluation_case_set,
)


def test_phase9_evaluation_case_set_is_valid_and_versioned():
    cases = list_evaluation_cases()

    assert EVALUATION_CASE_SET_VERSION == "phase-9-slice-2-v1"
    assert validate_evaluation_case_set() == []
    assert len(cases) == 5
    assert len({case.case_id for case in cases}) == len(cases)


def test_phase9_evaluation_case_set_covers_required_market_shapes():
    cases = list_evaluation_cases()
    symbols = {case.symbol for case in cases}
    categories = {case.category.value for case in cases}

    assert {"SPY", "QQQ"}.issubset(symbols)
    assert "mega-cap-equity" in categories
    assert "volatile-equity" in categories
    assert "index-oriented" in categories
    assert any(case.symbol == "SPX" and case.asset_type == AssetType.index for case in cases)


def test_phase9_evaluation_cases_build_deterministic_analysis_requests_only():
    for case in list_evaluation_cases():
        request = build_analysis_request(case)

        assert request.symbol == case.symbol
        assert request.analysis_date == case.analysis_date
        assert request.language == ReportLanguage.zh
        assert request.llm_provider == DETERMINISTIC_PROVIDER
        assert request.model == DETERMINISTIC_MODEL
        assert request.depth == case.depth
        assert request.analyst_set == case.analyst_set
        assert request.research_template == case.research_template


def test_phase9_evaluation_expectations_bind_to_deterministic_report_contract():
    for case in list_evaluation_cases():
        expectation = case.expectation

        assert "deterministic-tradingagents-fixture" in expectation.required_evidence_labels
        assert "options_observation" in expectation.required_report_sections
        assert "risk_factors" in expectation.required_report_sections
        assert "不生成自动交易指令" in expectation.required_safety_phrases
        assert "不生成实盘仓位" in expectation.required_safety_phrases
        assert expectation.minimum_confidence <= expectation.maximum_confidence


def test_phase9_evaluation_case_lookup_returns_known_case():
    case = get_evaluation_case("spy-macro-options-2026-06-18")

    assert case is not None
    assert case.symbol == "SPY"
