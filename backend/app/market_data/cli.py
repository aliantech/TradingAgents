import argparse
import json
import re

from app.core.config import settings
from app.db.session import SessionLocal, initialize_database
from app.market_data.sync_repository import ProviderSyncRepository


SECRET_LIKE_PATTERN = re.compile(r"(?i)(api[-_]?key|token|secret|password)=([^&\s]+)")


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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="aquantlens-market-data")
    subparsers = parser.add_subparsers(dest="command", required=True)
    list_runs_parser = subparsers.add_parser("list-sync-runs")
    list_runs_parser.add_argument("--provider", default=None)
    list_runs_parser.add_argument("--sync-type", default=None)
    list_runs_parser.add_argument("--limit", default=10, type=int)
    args = parser.parse_args(argv)

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
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
