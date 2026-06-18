from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.analysis.schemas import AnalysisDepth, AnalysisProgressEvent, AnalysisRequest, AssetType, ReportLanguage
from app.analysis.store import AnalysisRun
from app.db.models import AnalysisReportModel, AnalysisRunModel
from app.reports.schemas import ReportListItem, ResearchReport


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
