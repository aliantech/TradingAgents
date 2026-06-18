from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.analysis.schemas import AnalysisDepth, AnalysisProgressEvent, AnalysisRequest, AssetType, ReportLanguage
from app.analysis.store import AnalysisRun
from app.db.models import AnalysisReportModel, AnalysisRunModel
from app.reports.schemas import ReportComparison, ReportComparisonSection, ReportListItem, ReportRiskFactorChanges, ResearchReport


class AnalysisRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def save_run(self, run: AnalysisRun) -> AnalysisRun:
        model = AnalysisRunModel(
            id=run.analysis_id,
            symbol=run.request.symbol,
            asset_type=run.request.asset_type.value,
            analysis_date=run.request.analysis_date,
            language=run.request.language.value,
            llm_provider=run.request.llm_provider,
            model=run.request.model,
            depth=run.request.depth.value,
            analyst_set=run.request.analyst_set,
            research_template=run.request.research_template.value,
            status=run.status,
            progress=[event.model_dump() for event in run.progress],
            created_at=run.created_at,
            updated_at=run.updated_at,
        )
        if run.report is not None:
            report_id = run.report.report_id
            model.report = AnalysisReportModel(
                id=report_id,
                analysis_run_id=run.analysis_id,
                symbol=run.report.symbol,
                language=run.report.language,
                markdown=run.report.markdown or "",
                report_json=run.report.model_dump(mode="json"),
                confidence=run.report.confidence,
            )
        self.session.merge(model)
        self.session.commit()
        return run

    def get_run(self, analysis_id: UUID) -> AnalysisRun | None:
        model = self.session.get(AnalysisRunModel, analysis_id)
        if model is None:
            return None
        return self._to_run(model)

    def list_runs(self) -> list[AnalysisRun]:
        models = self.session.scalars(select(AnalysisRunModel).order_by(AnalysisRunModel.created_at.desc())).all()
        return [self._to_run(model) for model in models]

    def list_reports(self) -> list[ReportListItem]:
        models = self.session.scalars(select(AnalysisReportModel).order_by(AnalysisReportModel.created_at.desc())).all()
        return [
            ReportListItem(
                report_id=model.id,
                analysis_id=model.analysis_run_id,
                symbol=model.symbol,
                language=model.language,
                analyst_set=model.report_json.get("analyst_set", "macro-options"),
                research_template=model.report_json.get("research_template", "general"),
                summary=model.report_json["summary"],
                confidence=model.confidence,
            )
            for model in models
        ]

    def get_report(self, report_id: UUID) -> ResearchReport | None:
        model = self.session.get(AnalysisReportModel, report_id)
        if model is None:
            return None
        return ResearchReport(**model.report_json)

    def get_report_comparison(self, report_id: UUID) -> ReportComparison | None:
        current = self.session.get(AnalysisReportModel, report_id)
        if current is None:
            return None

        previous = self.session.scalars(
            select(AnalysisReportModel)
            .join(AnalysisRunModel)
            .where(AnalysisReportModel.id != current.id)
            .where(AnalysisReportModel.symbol == current.symbol)
            .where(AnalysisRunModel.analysis_date < current.run.analysis_date)
            .order_by(AnalysisRunModel.analysis_date.desc(), AnalysisReportModel.created_at.desc())
            .limit(1)
        ).first()
        if previous is None:
            return None

        return build_report_comparison(
            current=ResearchReport(**current.report_json),
            previous=ResearchReport(**previous.report_json),
        )

    def _to_run(self, model: AnalysisRunModel) -> AnalysisRun:
        request = AnalysisRequest(
            symbol=model.symbol,
            asset_type=AssetType(model.asset_type),
            analysis_date=model.analysis_date,
            language=ReportLanguage(model.language),
            llm_provider=model.llm_provider,
            model=model.model,
            depth=AnalysisDepth(model.depth),
            analyst_set=model.analyst_set,
            research_template=getattr(model, "research_template", "general"),
        )
        report = ResearchReport(**model.report.report_json) if model.report else None
        return AnalysisRun(
            analysis_id=model.id,
            request=request,
            status=model.status,
            progress=[AnalysisProgressEvent(**event) for event in model.progress],
            report=report,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )


COMPARISON_SECTION_FIELDS = (
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


def build_report_comparison(*, current: ResearchReport, previous: ResearchReport) -> ReportComparison:
    current_risks = set(current.risk_factors)
    previous_risks = set(previous.risk_factors)
    section_changes = {
        field: ReportComparisonSection(
            current=str(getattr(current, field)),
            previous=str(getattr(previous, field)),
            changed=getattr(current, field) != getattr(previous, field),
        )
        for field in COMPARISON_SECTION_FIELDS
    }
    return ReportComparison(
        symbol=current.symbol,
        current=_report_list_item(current),
        previous=_report_list_item(previous),
        confidence_delta=round(current.confidence - previous.confidence, 4),
        risk_factor_changes=ReportRiskFactorChanges(
            added=sorted(current_risks - previous_risks),
            removed=sorted(previous_risks - current_risks),
        ),
        section_changes=section_changes,
    )


def _report_list_item(report: ResearchReport) -> ReportListItem:
    return ReportListItem(
        report_id=report.report_id,
        analysis_id=report.analysis_id,
        symbol=report.symbol,
        language=report.language,
        analyst_set=report.analyst_set,
        research_template=report.research_template,
        summary=report.summary,
        confidence=report.confidence,
    )
