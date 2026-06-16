import argparse
import json
from datetime import date

from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import SessionLocal, initialize_database
from app.market_data.ingestion import MarketDataIngestionService
from app.market_data.provider_registry import get_market_data_provider
from app.market_data.repository import MarketDataRepository
from app.market_data.sync import MarketDataSyncResult, MarketDataSyncService
from app.market_data.sync_repository import ProviderSyncRepository


def run_sync_daily_bars(
    *,
    session: Session,
    provider_name: str,
    symbol: str,
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
    service = MarketDataSyncService(
        provider=provider,
        provider_name=provider_name,
        ingestion=MarketDataIngestionService(MarketDataRepository(session)),
        sync_repository=ProviderSyncRepository(session),
    )
    return service.sync_daily_bars(symbol, start, end)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="aquantlens-market-data")
    subparsers = parser.add_subparsers(dest="command", required=True)
    sync_parser = subparsers.add_parser("sync-daily-bars")
    sync_parser.add_argument("--symbol", required=True)
    sync_parser.add_argument("--start", required=True, type=date.fromisoformat)
    sync_parser.add_argument("--end", required=True, type=date.fromisoformat)
    sync_parser.add_argument("--provider", default=settings.market_data_provider)
    args = parser.parse_args(argv)

    if args.command == "sync-daily-bars":
        initialize_database()
        session = SessionLocal()
        try:
            result = run_sync_daily_bars(
                session=session,
                provider_name=args.provider,
                symbol=args.symbol,
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
