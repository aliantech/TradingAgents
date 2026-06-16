import argparse
import json
import re
from dataclasses import dataclass
from datetime import date

from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import SessionLocal, initialize_database
from app.market_data.ingestion import MarketDataIngestionService
from app.market_data.provider_readiness import check_market_data_provider_readiness
from app.market_data.provider_registry import get_market_data_provider
from app.market_data.repository import MarketDataRepository
from app.market_data.scheduler import run_configured_sync_targets_once, run_scheduler_loop
from app.market_data.sync import MarketDataSyncResult, MarketDataSyncService
from app.market_data.sync_repository import ProviderSyncRepository
from app.realtime.publisher_factory import create_market_data_publisher
from app.runtime_config import runtime_config


SECRET_LIKE_PATTERN = re.compile(r"(?i)(api[-_]?key|token|secret|password)=([^&\s]+)")


@dataclass(frozen=True)
class LiveProviderSmokeResult:
    provider: str
    symbol: str
    timeframe: str
    start: str
    end: str
    status: str
    rows_written: int
    missing: list[str]
    error_message: str | None = None


@dataclass(frozen=True)
class FinalLiveSmokeGateResult:
    provider: str
    symbol: str
    timeframe: str
    start: str
    end: str
    status: str
    readiness_ready: bool
    smoke_status: str | None
    rows_written: int
    audit_rows_found: int
    missing: list[str]
    error_message: str | None = None


def sanitize_cli_text(value: str | None) -> str | None:
    if value is None:
        return None
    return SECRET_LIKE_PATTERN.sub(lambda match: f"{match.group(1)}=***", value)


def sync_type_for_timeframe(timeframe: str) -> str:
    return "daily_bars" if timeframe == "1d" else f"bars_{timeframe}"


def sync_runs_payload(runs) -> list[dict]:
    return [
        {
            "id": str(run.id),
            "provider": run.provider,
            "sync_type": run.sync_type,
            "status": run.status,
            "started_at": run.started_at.isoformat(),
            "finished_at": run.finished_at.isoformat() if run.finished_at else None,
            "rows_written": run.rows_written,
            "error_message": sanitize_cli_text(run.error_message),
        }
        for run in runs
    ]


def run_sync_bars(
    *,
    session: Session,
    provider_name: str,
    symbol: str,
    timeframe: str,
    start: date,
    end: date,
) -> MarketDataSyncResult:
    provider = get_market_data_provider(
        provider_name,
        polygon_api_key=runtime_config.polygon_api_key(settings),
        polygon_base_url=runtime_config.polygon_base_url(settings),
        max_retries=settings.provider_max_retries,
        retry_backoff_seconds=settings.provider_retry_backoff_seconds,
    )
    publisher = create_market_data_publisher(
        enabled=settings.realtime_market_publish_enabled,
        redis_url=settings.redis_url,
        ttl_seconds=settings.realtime_market_ttl_seconds,
    )
    service = MarketDataSyncService(
        provider=provider,
        provider_name=provider_name,
        ingestion=MarketDataIngestionService(MarketDataRepository(session), publisher=publisher),
        sync_repository=ProviderSyncRepository(session),
    )
    return service.sync_bars(symbol, timeframe, start, end)


def run_sync_daily_bars(
    *,
    session: Session,
    provider_name: str,
    symbol: str,
    start: date,
    end: date,
) -> MarketDataSyncResult:
    return run_sync_bars(
        session=session,
        provider_name=provider_name,
        symbol=symbol,
        timeframe="1d",
        start=start,
        end=end,
    )


def run_live_provider_smoke(
    *,
    session: Session,
    provider_name: str,
    symbol: str,
    timeframe: str,
    start: date,
    end: date,
) -> LiveProviderSmokeResult:
    normalized_symbol = symbol.upper()
    readiness = check_market_data_provider_readiness(settings, provider=provider_name)
    if not readiness.ready:
        return LiveProviderSmokeResult(
            provider=readiness.provider,
            symbol=normalized_symbol,
            timeframe=timeframe,
            start=start.isoformat(),
            end=end.isoformat(),
            status="not_ready",
            rows_written=0,
            missing=readiness.missing,
            error_message=readiness.message,
        )
    result = run_sync_bars(
        session=session,
        provider_name=readiness.provider,
        symbol=normalized_symbol,
        timeframe=timeframe,
        start=start,
        end=end,
    )
    return LiveProviderSmokeResult(
        provider=readiness.provider,
        symbol=normalized_symbol,
        timeframe=timeframe,
        start=start.isoformat(),
        end=end.isoformat(),
        status=result.status,
        rows_written=result.rows_written,
        missing=[],
        error_message=result.error_message,
    )


def run_final_live_smoke_gate(
    *,
    session: Session,
    provider_name: str,
    symbol: str,
    timeframe: str,
    start: date,
    end: date,
) -> FinalLiveSmokeGateResult:
    normalized_symbol = symbol.upper()
    readiness = check_market_data_provider_readiness(settings, provider=provider_name)
    if not readiness.ready:
        return FinalLiveSmokeGateResult(
            provider=readiness.provider,
            symbol=normalized_symbol,
            timeframe=timeframe,
            start=start.isoformat(),
            end=end.isoformat(),
            status="not_ready",
            readiness_ready=False,
            smoke_status=None,
            rows_written=0,
            audit_rows_found=0,
            missing=readiness.missing,
            error_message=readiness.message,
        )

    smoke = run_live_provider_smoke(
        session=session,
        provider_name=readiness.provider,
        symbol=normalized_symbol,
        timeframe=timeframe,
        start=start,
        end=end,
    )
    audit_rows = ProviderSyncRepository(session).list_runs(
        limit=5,
        provider=readiness.provider,
        sync_type=sync_type_for_timeframe(timeframe),
    )
    audit_rows_found = len(audit_rows)
    status = "succeeded" if smoke.status == "succeeded" and audit_rows_found > 0 else "audit_missing"
    if smoke.status != "succeeded":
        status = smoke.status
    return FinalLiveSmokeGateResult(
        provider=readiness.provider,
        symbol=normalized_symbol,
        timeframe=timeframe,
        start=start.isoformat(),
        end=end.isoformat(),
        status=status,
        readiness_ready=True,
        smoke_status=smoke.status,
        rows_written=smoke.rows_written,
        audit_rows_found=audit_rows_found,
        missing=smoke.missing,
        error_message=sanitize_cli_text(smoke.error_message),
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="aquantlens-market-data")
    subparsers = parser.add_subparsers(dest="command", required=True)
    sync_parser = subparsers.add_parser("sync-daily-bars")
    sync_parser.add_argument("--symbol", required=True)
    sync_parser.add_argument("--start", required=True, type=date.fromisoformat)
    sync_parser.add_argument("--end", required=True, type=date.fromisoformat)
    sync_parser.add_argument("--timeframe", default="1d", choices=["1m", "5m", "1d"])
    sync_parser.add_argument("--provider", default=settings.market_data_provider)
    scheduler_parser = subparsers.add_parser("run-scheduler-once")
    scheduler_parser.add_argument("--targets", default=settings.scheduler_targets)
    scheduler_parser.add_argument("--today", default=date.today(), type=date.fromisoformat)
    scheduler_parser.add_argument("--provider", default=settings.market_data_provider)
    scheduler_loop_parser = subparsers.add_parser("run-scheduler-loop")
    scheduler_loop_parser.add_argument("--targets", default=settings.scheduler_targets)
    scheduler_loop_parser.add_argument("--today", default=None, type=date.fromisoformat)
    scheduler_loop_parser.add_argument("--provider", default=settings.market_data_provider)
    scheduler_loop_parser.add_argument("--interval-seconds", default=settings.scheduler_interval_seconds, type=int)
    scheduler_loop_parser.add_argument("--max-iterations", default=None, type=int)
    readiness_parser = subparsers.add_parser("provider-readiness")
    readiness_parser.add_argument("--provider", default=settings.market_data_provider)
    live_smoke_parser = subparsers.add_parser("live-provider-smoke")
    live_smoke_parser.add_argument("--provider", default=settings.market_data_provider)
    live_smoke_parser.add_argument("--symbol", required=True)
    live_smoke_parser.add_argument("--timeframe", default="1d", choices=["1m", "5m", "1d"])
    live_smoke_parser.add_argument("--start", required=True, type=date.fromisoformat)
    live_smoke_parser.add_argument("--end", required=True, type=date.fromisoformat)
    list_runs_parser = subparsers.add_parser("list-sync-runs")
    list_runs_parser.add_argument("--provider", default=None)
    list_runs_parser.add_argument("--sync-type", default=None)
    list_runs_parser.add_argument("--limit", default=10, type=int)
    final_gate_parser = subparsers.add_parser("final-live-smoke-gate")
    final_gate_parser.add_argument("--provider", default=settings.market_data_provider)
    final_gate_parser.add_argument("--symbol", required=True)
    final_gate_parser.add_argument("--timeframe", default="1d", choices=["1m", "5m", "1d"])
    final_gate_parser.add_argument("--start", required=True, type=date.fromisoformat)
    final_gate_parser.add_argument("--end", required=True, type=date.fromisoformat)
    args = parser.parse_args(argv)

    if args.command == "sync-daily-bars":
        initialize_database()
        session = SessionLocal()
        try:
            result = run_sync_bars(
                session=session,
                provider_name=args.provider,
                symbol=args.symbol,
                timeframe=args.timeframe,
                start=args.start,
                end=args.end,
            )
        finally:
            session.close()
        print(json.dumps(result.__dict__, ensure_ascii=False))
        return 0 if result.status == "succeeded" else 1
    if args.command == "run-scheduler-once":
        initialize_database()
        session = SessionLocal()
        try:
            results = run_configured_sync_targets_once(
                session=session,
                provider_name=args.provider,
                target_config=args.targets,
                today=args.today,
            )
        finally:
            session.close()
        print(json.dumps([result.__dict__ for result in results], ensure_ascii=False))
        return 0 if all(result.status == "succeeded" for result in results) else 1
    if args.command == "run-scheduler-loop":
        initialize_database()
        iterations = run_scheduler_loop(
            session_factory=SessionLocal,
            provider_name=args.provider,
            target_config=args.targets,
            interval_seconds=args.interval_seconds,
            today_fn=(lambda: args.today or date.today()),
            max_iterations=args.max_iterations,
        )
        payload = [
            {
                "iteration": iteration.iteration,
                "results": [result.__dict__ for result in iteration.results],
            }
            for iteration in iterations
        ]
        print(json.dumps(payload, ensure_ascii=False))
        return 0 if all(result.status == "succeeded" for iteration in iterations for result in iteration.results) else 1
    if args.command == "provider-readiness":
        readiness = check_market_data_provider_readiness(settings, provider=args.provider)
        print(json.dumps(readiness.__dict__, ensure_ascii=False))
        return 0 if readiness.ready else 1
    if args.command == "live-provider-smoke":
        initialize_database()
        session = SessionLocal()
        try:
            result = run_live_provider_smoke(
                session=session,
                provider_name=args.provider,
                symbol=args.symbol,
                timeframe=args.timeframe,
                start=args.start,
                end=args.end,
            )
        finally:
            session.close()
        print(json.dumps(result.__dict__, ensure_ascii=False))
        return 0 if result.status == "succeeded" else 1
    if args.command == "list-sync-runs":
        initialize_database()
        session = SessionLocal()
        try:
            runs = ProviderSyncRepository(session).list_runs(
                limit=args.limit,
                provider=args.provider,
                sync_type=args.sync_type,
            )
        finally:
            session.close()
        payload = sync_runs_payload(runs)
        print(json.dumps(payload, ensure_ascii=False))
        return 0
    if args.command == "final-live-smoke-gate":
        initialize_database()
        session = SessionLocal()
        try:
            result = run_final_live_smoke_gate(
                session=session,
                provider_name=args.provider,
                symbol=args.symbol,
                timeframe=args.timeframe,
                start=args.start,
                end=args.end,
            )
        finally:
            session.close()
        print(json.dumps(result.__dict__, ensure_ascii=False))
        return 0 if result.status == "succeeded" else 1
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
