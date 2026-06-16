from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import ProviderSyncRunModel


@dataclass(frozen=True)
class ProviderSyncRun:
    id: UUID
    provider: str
    sync_type: str
    status: str
    started_at: datetime
    finished_at: datetime | None
    rows_written: int
    error_message: str | None


@dataclass(frozen=True)
class ProviderSyncSummary:
    total_runs: int
    succeeded: int
    failed: int
    rows_written: int
    latest_status: str | None
    latest_finished_at: datetime | None
    average_duration_ms: int


class ProviderSyncRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def record_run(
        self,
        *,
        provider: str,
        sync_type: str,
        status: str,
        started_at: datetime,
        finished_at: datetime | None,
        rows_written: int,
        error_message: str | None = None,
    ) -> ProviderSyncRun:
        model = ProviderSyncRunModel(
            provider=provider,
            sync_type=sync_type,
            status=status,
            started_at=started_at,
            finished_at=finished_at,
            rows_written=rows_written,
            error_message=error_message,
        )
        self.session.add(model)
        self.session.commit()
        self.session.refresh(model)
        return self._to_schema(model)

    def list_runs(self, *, limit: int = 100) -> list[ProviderSyncRun]:
        statement = select(ProviderSyncRunModel).order_by(ProviderSyncRunModel.started_at.desc()).limit(limit)
        models = self.session.scalars(statement).all()
        return [self._to_schema(model) for model in models]

    def summarize_runs(self) -> ProviderSyncSummary:
        runs = self.list_runs(limit=1000)
        durations_ms = [
            int((run.finished_at - run.started_at).total_seconds() * 1000)
            for run in runs
            if run.finished_at is not None
        ]
        latest = runs[0] if runs else None
        return ProviderSyncSummary(
            total_runs=len(runs),
            succeeded=sum(1 for run in runs if run.status == "succeeded"),
            failed=sum(1 for run in runs if run.status == "failed"),
            rows_written=sum(run.rows_written for run in runs),
            latest_status=latest.status if latest else None,
            latest_finished_at=latest.finished_at if latest else None,
            average_duration_ms=int(sum(durations_ms) / len(durations_ms)) if durations_ms else 0,
        )

    def _to_schema(self, model: ProviderSyncRunModel) -> ProviderSyncRun:
        return ProviderSyncRun(
            id=model.id,
            provider=model.provider,
            sync_type=model.sync_type,
            status=model.status,
            started_at=model.started_at,
            finished_at=model.finished_at,
            rows_written=model.rows_written,
            error_message=model.error_message,
        )
