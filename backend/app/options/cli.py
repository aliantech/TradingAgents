import argparse
import json
from dataclasses import asdict
from datetime import date

from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import SessionLocal, initialize_database
from app.market_data.provider_readiness import check_market_data_provider_readiness
from app.market_data.sync_repository import ProviderSyncRepository
from app.options.polygon_provider import OptionChainProvider, PolygonOptionsProvider
from app.options.repository import OptionRepository
from app.options.sync import OptionChainSyncResult, OptionChainSyncService


def run_sync_chain(
    *,
    session: Session,
    provider: OptionChainProvider,
    provider_name: str,
    underlying_symbol: str,
    expiry: date,
    limit: int,
) -> OptionChainSyncResult:
    service = OptionChainSyncService(
        provider=provider,
        provider_name=provider_name,
        option_repository=OptionRepository(session),
        sync_repository=ProviderSyncRepository(session),
    )
    return service.sync_chain(
        underlying_symbol=underlying_symbol,
        expiry=expiry,
        limit=limit,
    )


def create_options_provider(provider_name: str) -> OptionChainProvider:
    normalized_provider = provider_name.lower()
    if normalized_provider != "polygon":
        raise ValueError(f"Unsupported options provider: {provider_name}.")
    return PolygonOptionsProvider(
        api_key=settings.polygon_api_key,
        base_url=settings.polygon_base_url,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="aquantlens-options")
    subparsers = parser.add_subparsers(dest="command", required=True)
    sync_parser = subparsers.add_parser("sync-chain")
    sync_parser.add_argument("--underlying", required=True)
    sync_parser.add_argument("--expiry", required=True, type=date.fromisoformat)
    sync_parser.add_argument("--provider", default="polygon")
    sync_parser.add_argument("--limit", default=250, type=int)
    args = parser.parse_args(argv)

    if args.command == "sync-chain":
        readiness = check_market_data_provider_readiness(settings, provider=args.provider)
        if not readiness.ready:
            print(
                json.dumps(
                    {
                        "provider": readiness.provider,
                        "underlying_symbol": args.underlying.upper(),
                        "expiry": args.expiry.isoformat(),
                        "status": "not_ready",
                        "readiness_ready": False,
                        "rows_written": 0,
                        "missing": readiness.missing,
                        "error_message": readiness.message,
                    },
                    ensure_ascii=False,
                )
            )
            return 1
        initialize_database()
        session = SessionLocal()
        try:
            provider = create_options_provider(readiness.provider)
            result = run_sync_chain(
                session=session,
                provider=provider,
                provider_name=readiness.provider,
                underlying_symbol=args.underlying,
                expiry=args.expiry,
                limit=args.limit,
            )
        finally:
            session.close()
        payload = asdict(result) | {"readiness_ready": True, "missing": []}
        print(json.dumps(payload, ensure_ascii=False))
        return 0 if result.status == "succeeded" else 1
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
