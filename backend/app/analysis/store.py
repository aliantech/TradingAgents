from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID

from app.analysis.schemas import AnalysisProgressEvent, AnalysisRequest
from app.reports.schemas import ResearchReport


@dataclass
class AnalysisRun:
    analysis_id: UUID
    request: AnalysisRequest
    status: str
    progress: list[AnalysisProgressEvent] = field(default_factory=list)
    report: ResearchReport | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))


class InMemoryAnalysisStore:
    def __init__(self) -> None:
        self._runs: dict[UUID, AnalysisRun] = {}

    def save(self, run: AnalysisRun) -> AnalysisRun:
        self._runs[run.analysis_id] = run
        return run

    def get(self, analysis_id: UUID) -> AnalysisRun | None:
        return self._runs.get(analysis_id)

    def list_runs(self) -> list[AnalysisRun]:
        return list(self._runs.values())


analysis_store = InMemoryAnalysisStore()
