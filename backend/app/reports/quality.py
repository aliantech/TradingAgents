from dataclasses import dataclass

from app.reports.schemas import ResearchReport


class ReportQualityError(ValueError):
    pass


@dataclass(frozen=True)
class ReportQualityIssue:
    field: str
    message: str


REQUIRED_TEXT_FIELDS = (
    "summary",
    "market_background",
    "fundamental_analysis",
    "technical_analysis",
    "sentiment_analysis",
    "options_observation",
    "bull_case",
    "bear_case",
    "trade_plan",
    "position_sizing",
    "take_profit_stop_loss",
)

NO_TRADING_AUTHORITY_TERMS = ("研究", "不生成", "不代表", "观察", "参考")


def validate_research_report_quality(report: ResearchReport) -> None:
    issues = research_report_quality_issues(report)
    if issues:
        summary = "; ".join(f"{issue.field}: {issue.message}" for issue in issues)
        raise ReportQualityError(f"Report quality validation failed: {summary}")


def research_report_quality_issues(report: ResearchReport) -> list[ReportQualityIssue]:
    issues: list[ReportQualityIssue] = []
    if report.language != "zh":
        issues.append(ReportQualityIssue("language", "expected Chinese-first report language zh"))

    for field in REQUIRED_TEXT_FIELDS:
        value = str(getattr(report, field))
        if not value.strip():
            issues.append(ReportQualityIssue(field, "required section is empty"))
            continue
        if report.language == "zh" and not contains_chinese_text(value):
            issues.append(ReportQualityIssue(field, "required Chinese-first section has no Chinese text"))

    if not report.risk_factors:
        issues.append(ReportQualityIssue("risk_factors", "at least one risk factor is required"))
    if not report.evidence_labels:
        issues.append(ReportQualityIssue("evidence_labels", "at least one evidence label is required"))
    if not 0 <= report.confidence <= 1:
        issues.append(ReportQualityIssue("confidence", "confidence must be between 0 and 1"))
    if not contains_no_trading_authority_language(report):
        issues.append(
            ReportQualityIssue(
                "trade_authority",
                "report must state research-only or no-trading-authority language",
            )
        )
    return issues


def contains_chinese_text(value: str) -> bool:
    return any("\u4e00" <= char <= "\u9fff" for char in value)


def contains_no_trading_authority_language(report: ResearchReport) -> bool:
    text = "\n".join((report.trade_plan, report.position_sizing, report.take_profit_stop_loss))
    return any(term in text for term in NO_TRADING_AUTHORITY_TERMS)
