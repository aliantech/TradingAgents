from app.analysis.diagnostics import build_failure_diagnostic
from app.analysis.schemas import AnalysisProgressEvent


def test_failure_diagnostic_classifies_provider_errors_and_redacts_message():
    diagnostic = build_failure_diagnostic(
        [
            AnalysisProgressEvent(step="queued", status="completed", message="queued"),
            AnalysisProgressEvent(
                step="tradingagents",
                status="failed",
                message="OpenAI provider timeout api_key=sk-secret Bearer abc.def",
            ),
        ]
    )

    assert diagnostic is not None
    assert diagnostic.category == "provider"
    assert diagnostic.failed_step == "tradingagents"
    assert "sk-secret" not in diagnostic.message
    assert "Bearer abc.def" not in diagnostic.message
    assert "[redacted]" in diagnostic.message
    assert "retry" in diagnostic.retry_guidance.lower()


def test_failure_diagnostic_classifies_model_errors():
    diagnostic = build_failure_diagnostic(
        [AnalysisProgressEvent(step="tradingagents", status="failed", message="unsupported model name")]
    )

    assert diagnostic is not None
    assert diagnostic.category == "model"


def test_failure_diagnostic_classifies_report_quality_errors():
    diagnostic = build_failure_diagnostic(
        [AnalysisProgressEvent(step="report_quality", status="failed", message="Report quality validation failed")]
    )

    assert diagnostic is not None
    assert diagnostic.category == "report_quality"


def test_failure_diagnostic_returns_none_without_failed_event():
    assert build_failure_diagnostic([AnalysisProgressEvent(step="report", status="completed", message="ok")]) is None
