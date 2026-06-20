from app.analysis.schemas import AnalysisFailureDiagnostic, AnalysisProgressEvent
from app.analysis.tradingagents_adapter import sanitize_error_message


RETRY_GUIDANCE: dict[str, str] = {
    "provider": "Check provider readiness, rate limits, network access, and saved runner settings before retrying manually.",
    "model": "Check the selected provider/model names in Settings before retrying manually.",
    "runtime": "Check TradingAgents runtime configuration and server logs before retrying manually.",
    "report_quality": "Inspect the generated report sections and evidence labels, then retry after the runner output is corrected.",
    "unknown": "Inspect the failed progress event and retry manually only after the cause is understood.",
}


def build_failure_diagnostic(progress: list[AnalysisProgressEvent]) -> AnalysisFailureDiagnostic | None:
    failed_event = next((event for event in reversed(progress) if event.status == "failed"), None)
    if failed_event is None:
        return None
    category = classify_failure(failed_event)
    return AnalysisFailureDiagnostic(
        category=category,
        failed_step=failed_event.step,
        message=sanitize_error_message(failed_event.message),
        retry_guidance=RETRY_GUIDANCE[category],
    )


def classify_failure(event: AnalysisProgressEvent) -> str:
    text = f"{event.step} {event.message}".lower()
    if event.step == "report_quality" or "report quality" in text:
        return "report_quality"
    if any(term in text for term in ("provider", "api", "rate limit", "timeout", "network", "connection")):
        return "provider"
    if any(term in text for term in ("model", "llm", "context length", "unsupported")):
        return "model"
    if any(term in text for term in ("runtime", "import", "config", "disabled", "tradingagents")):
        return "runtime"
    return "unknown"
