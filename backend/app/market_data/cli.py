import argparse
import json
from datetime import date

from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import SessionLocal, initialize_database
from app.market_data.ingestion import MarketDataIngestionService
from app.market_data.provider_registry import get_market_data_provider
from app.market_data.repository import MarketDataRepository
from app.market_data.scheduler import run_configured_sync_targets_once
from app.market_data.sync import MarketDataSyncResult, MarketDataSyncService
from app.market_data.sync_repository import ProviderSyncRepository
from app.realtime.publisher_factory import create_market_data_publisher


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
        polygon_api_key=settings.polygon_api_key,
        polygon_base_url=settings.polygon_base_url,
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
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
