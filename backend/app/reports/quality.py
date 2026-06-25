from dataclasses import dataclass
import re

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
REAL_RUNNER_LABEL = "tradingagents-real-runner"
VERIFIED_SNAPSHOT_LABEL = "finance-data-hub-verified-snapshot"
SNAPSHOT_DATE_RE = re.compile(r"Latest trading row used:\s*([0-9]{4}-[0-9]{2}-[0-9]{2})")
SNAPSHOT_CLOSE_RE = re.compile(r"^\|\s*Close\s*\|\s*([0-9,]+(?:\.[0-9]+)?)\s*\|", re.MULTILINE)
NUMERIC_RE = re.compile(r"(?<![0-9])([0-9]{2,5}(?:\.[0-9]+)?)(?![0-9])")


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
    issues.extend(market_data_grounding_issues(report))
    return issues


def contains_chinese_text(value: str) -> bool:
    return any("\u4e00" <= char <= "\u9fff" for char in value)


def contains_no_trading_authority_language(report: ResearchReport) -> bool:
    text = "\n".join((report.trade_plan, report.position_sizing, report.take_profit_stop_loss))
    return any(term in text for term in NO_TRADING_AUTHORITY_TERMS)


def market_data_grounding_issues(report: ResearchReport) -> list[ReportQualityIssue]:
    if REAL_RUNNER_LABEL not in report.evidence_labels:
        return []
    if VERIFIED_SNAPSHOT_LABEL not in report.evidence_labels:
        return [
            ReportQualityIssue(
                "market_data_grounding",
                "real-runner reports must include a verified market-data snapshot evidence label",
            )
        ]

    markdown = report.markdown or ""
    snapshot_date = extract_snapshot_date(markdown)
    snapshot_close = extract_snapshot_close(markdown)
    if snapshot_date is None or snapshot_close is None:
        return [
            ReportQualityIssue(
                "market_data_grounding",
                "real-runner reports must include latest verified date and close in markdown",
            )
        ]

    conflicts = close_claim_conflicts(report, snapshot_date, snapshot_close)
    if conflicts:
        return [
            ReportQualityIssue(
                "market_data_grounding",
                f"close claim conflicts with verified snapshot close {snapshot_close:.2f}: {conflicts[0]}",
            )
        ]
    return []


def extract_snapshot_date(markdown: str) -> str | None:
    match = SNAPSHOT_DATE_RE.search(markdown)
    return match.group(1) if match else None


def extract_snapshot_close(markdown: str) -> float | None:
    match = SNAPSHOT_CLOSE_RE.search(markdown)
    if not match:
        return None
    return float(match.group(1).replace(",", ""))


def close_claim_conflicts(report: ResearchReport, snapshot_date: str, snapshot_close: float) -> list[str]:
    text = "\n".join(
        (
            report.market_background,
            report.technical_analysis,
            report.markdown or "",
        )
    )
    conflicts: list[str] = []
    for line in text.splitlines():
        lower_line = line.lower()
        if snapshot_date not in line:
            continue
        if "close" not in lower_line and "收盘" not in line:
            continue
        for match in NUMERIC_RE.finditer(line):
            value = float(match.group(1).replace(",", ""))
            if abs(value - snapshot_close) > 0.01:
                conflicts.append(line.strip())
                break
    return conflicts
