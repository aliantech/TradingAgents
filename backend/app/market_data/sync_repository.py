from dataclasses import dataclass
from datetime import UTC, datetime
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


@dataclass(frozen=True)
class ProviderSyncSummaryGroup:
    provider: str
    sync_type: str
    total_runs: int
    succeeded: int
    failed: int
    rows_written: int
    latest_status: str | None
    latest_finished_at: datetime | None
    average_duration_ms: int


@dataclass(frozen=True)
class ProviderSyncHealth:
    provider: str
    sync_type: str
    status: str
    total_runs: int
    failed_runs: int
    failure_rate: float
    latest_status: str | None
    latest_finished_at: datetime | None
    minutes_since_latest: int | None
    stale_after_minutes: int
    message: str


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

    def list_runs(
        self,
        *,
        limit: int = 100,
        provider: str | None = None,
        sync_type: str | None = None,
        started_after: datetime | None = None,
        started_before: datetime | None = None,
    ) -> list[ProviderSyncRun]:
        statement = select(ProviderSyncRunModel)
        if provider:
            statement = statement.where(ProviderSyncRunModel.provider == provider)
        if sync_type:
            statement = statement.where(ProviderSyncRunModel.sync_type == sync_type)
        if started_after:
            statement = statement.where(ProviderSyncRunModel.started_at >= started_after)
        if started_before:
            statement = statement.where(ProviderSyncRunModel.started_at <= started_before)
        statement = statement.order_by(ProviderSyncRunModel.started_at.desc()).limit(limit)
        models = self.session.scalars(statement).all()
        return [self._to_schema(model) for model in models]

    def summarize_runs(
        self,
        *,
        provider: str | None = None,
        sync_type: str | None = None,
        started_after: datetime | None = None,
        started_before: datetime | None = None,
    ) -> ProviderSyncSummary:
        runs = self.list_runs(
            limit=1000,
            provider=provider,
            sync_type=sync_type,
            started_after=started_after,
            started_before=started_before,
        )
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

    def summarize_groups(
        self,
        *,
        provider: str | None = None,
        sync_type: str | None = None,
        started_after: datetime | None = None,
        started_before: datetime | None = None,
    ) -> list[ProviderSyncSummaryGroup]:
        runs = self.list_runs(
            limit=1000,
            provider=provider,
            sync_type=sync_type,
            started_after=started_after,
            started_before=started_before,
        )
        grouped: dict[tuple[str, str], list[ProviderSyncRun]] = {}
        for run in runs:
            grouped.setdefault((run.provider, run.sync_type), []).append(run)
        groups: list[ProviderSyncSummaryGroup] = []
        for (group_provider, group_sync_type), group_runs in grouped.items():
            durations_ms = [
                int((run.finished_at - run.started_at).total_seconds() * 1000)
                for run in group_runs
                if run.finished_at is not None
            ]
            latest = group_runs[0]
            groups.append(
                ProviderSyncSummaryGroup(
                    provider=group_provider,
                    sync_type=group_sync_type,
                    total_runs=len(group_runs),
                    succeeded=sum(1 for run in group_runs if run.status == "succeeded"),
                    failed=sum(1 for run in group_runs if run.status == "failed"),
                    rows_written=sum(run.rows_written for run in group_runs),
                    latest_status=latest.status,
                    latest_finished_at=latest.finished_at,
                    average_duration_ms=int(sum(durations_ms) / len(durations_ms)) if durations_ms else 0,
                )
            )
        return sorted(groups, key=lambda group: (group.provider, group.sync_type))

    def evaluate_health(
        self,
        *,
        provider: str,
        sync_type: str,
        now: datetime,
        stale_after_minutes: int,
        failure_rate_threshold: float,
    ) -> ProviderSyncHealth:
        runs = self.list_runs(limit=1000, provider=provider, sync_type=sync_type)
        if not runs:
            return ProviderSyncHealth(
                provider=provider,
                sync_type=sync_type,
                status="missing",
                total_runs=0,
                failed_runs=0,
                failure_rate=0.0,
                latest_status=None,
                latest_finished_at=None,
                minutes_since_latest=None,
                stale_after_minutes=stale_after_minutes,
                message="No sync runs found for this target.",
            )

        latest = runs[0]
        failed_runs = sum(1 for run in runs if run.status == "failed")
        failure_rate = failed_runs / len(runs)
        latest_finished_at = _as_utc(latest.finished_at) if latest.finished_at is not None else None
        minutes_since_latest = int((_as_utc(now) - latest_finished_at).total_seconds() // 60) if latest_finished_at else None

        if latest.status == "failed":
            status = "failing"
            message = "Latest sync failed."
        elif failure_rate >= failure_rate_threshold and failed_runs > 0:
            status = "failing"
            message = f"Failure rate is at or above {failure_rate_threshold:.0%}."
        elif minutes_since_latest is not None and minutes_since_latest > stale_after_minutes:
            status = "stale"
            message = f"Latest successful sync is older than {stale_after_minutes} minutes."
        else:
            status = "ok"
            message = "Sync target is healthy."

        return ProviderSyncHealth(
            provider=provider,
            sync_type=sync_type,
            status=status,
            total_runs=len(runs),
            failed_runs=failed_runs,
            failure_rate=round(failure_rate, 4),
            latest_status=latest.status,
            latest_finished_at=latest_finished_at,
            minutes_since_latest=minutes_since_latest,
            stale_after_minutes=stale_after_minutes,
            message=message,
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


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)
