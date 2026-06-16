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
