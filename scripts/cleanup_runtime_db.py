#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = REPO_ROOT / "backend" / "aquantlens_us.db"
MOCK_SYMBOL_RE = re.compile(r"^T[0-9A-F]{7}$")
LEGACY_MOCK_SUMMARY_RE = re.compile(r"^[A-Z0-9.]+ 当前趋势中性偏强，但需要结合 IV、成交量和宏观事件确认方向。$")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Clean mock/test/legacy rows from the AQuantLens runtime SQLite DB.")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB, help=f"Runtime DB path. Default: {DEFAULT_DB}")
    parser.add_argument("--execute", action="store_true", help="Apply deletes. Without this flag, the script is dry-run only.")
    parser.add_argument("--no-backup", action="store_true", help="Skip SQLite backup when --execute is used.")
    parser.add_argument("--keep-failed-analysis", action="store_true", help="Keep failed analysis runs without reports.")
    parser.add_argument("--keep-legacy-options-audit", action="store_true", help="Keep old polygon options audit rows missing target symbol/expiry.")
    parser.add_argument("--keep-pre-2026-06-19-sync", action="store_true", help="Keep provider sync audit rows created before 2026-06-19.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    db_path = args.db.resolve()
    if not db_path.exists():
        raise SystemExit(f"DB not found: {db_path}")
    if db_path.name != "aquantlens_us.db":
        raise SystemExit(f"Refusing to clean unexpected DB filename: {db_path}")

    backup_path = None
    if args.execute and not args.no_backup:
        backup_path = backup_database(db_path)

    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    try:
        before = counts(connection)
        plan = build_cleanup_plan(connection, keep_failed_analysis=args.keep_failed_analysis)
        sync_where, sync_params = sync_cleanup_predicate(
            keep_legacy_options_audit=args.keep_legacy_options_audit,
            keep_pre_2026_06_19_sync=args.keep_pre_2026_06_19_sync,
        )
        sync_count = connection.execute(f"select count(*) from provider_sync_runs where {sync_where}", sync_params).fetchone()[0]

        result = {
            "mode": "execute" if args.execute else "dry-run",
            "db": str(db_path),
            "backup": str(backup_path) if backup_path else None,
            "before": before,
            "planned_delete": {
                "analysis_reports": len(plan["report_ids"]),
                "analysis_runs": len(plan["run_ids"]),
                "provider_sync_runs": sync_count,
            },
        }

        if args.execute:
            apply_cleanup(connection, plan, sync_where, sync_params)
            connection.commit()
            result["after"] = counts(connection)

        print(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True))
    finally:
        connection.close()
    return 0


def backup_database(db_path: Path) -> Path:
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_dir = db_path.parent / "backups" / f"cleanup-{stamp}"
    backup_dir.mkdir(parents=True, exist_ok=True)
    backup_path = backup_dir / db_path.name
    with sqlite3.connect(db_path) as source, sqlite3.connect(backup_path) as destination:
        source.backup(destination)
    for suffix in ("-wal", "-shm"):
        sidecar = db_path.with_name(f"{db_path.name}{suffix}")
        if sidecar.exists():
            shutil.copy2(sidecar, backup_dir / sidecar.name)
    return backup_path


def counts(connection: sqlite3.Connection) -> dict[str, int]:
    return {
        "analysis_runs": table_count(connection, "analysis_runs"),
        "analysis_reports": table_count(connection, "analysis_reports"),
        "provider_sync_runs": table_count(connection, "provider_sync_runs"),
        "option_contracts": table_count(connection, "option_contracts"),
        "option_snapshots": table_count(connection, "option_snapshots"),
    }


def table_count(connection: sqlite3.Connection, table: str) -> int:
    return int(connection.execute(f"select count(*) from {table}").fetchone()[0])


def build_cleanup_plan(connection: sqlite3.Connection, *, keep_failed_analysis: bool) -> dict[str, set[str]]:
    run_ids: set[str] = set()
    report_ids: set[str] = set()

    for row in connection.execute("select id, analysis_run_id, report_json from analysis_reports"):
        report = load_json(row["report_json"])
        if is_legacy_mock_report(report):
            report_ids.add(row["id"])
            run_ids.add(row["analysis_run_id"])

    report_run_ids = {
        row["analysis_run_id"]
        for row in connection.execute("select analysis_run_id from analysis_reports")
    }
    for row in connection.execute("select id, symbol, status, created_at from analysis_runs"):
        symbol = row["symbol"] or ""
        created_at = row["created_at"] or ""
        if MOCK_SYMBOL_RE.match(symbol):
            run_ids.add(row["id"])
        elif row["status"] == "completed" and created_at[:10] < "2026-06-19":
            run_ids.add(row["id"])
        elif not keep_failed_analysis and row["id"] not in report_run_ids:
            run_ids.add(row["id"])

    for row in connection.execute("select id from analysis_reports where analysis_run_id in (%s)" % placeholders(run_ids), tuple(run_ids)) if run_ids else []:
        report_ids.add(row["id"])

    return {"run_ids": run_ids, "report_ids": report_ids}


def load_json(value: str | bytes | None) -> dict:
    if not value:
        return {}
    if isinstance(value, bytes):
        value = value.decode()
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def is_legacy_mock_report(report: dict) -> bool:
    summary = str(report.get("summary", ""))
    if LEGACY_MOCK_SUMMARY_RE.match(summary):
        return True
    if report.get("sentiment_analysis") == "新闻与市场情绪暂按中性处理，等待外部新闻源接入后增强。":
        return True
    evidence = report.get("evidence_labels")
    if isinstance(evidence, list) and "AQuantLens Phase 1 sample report" in evidence:
        return True
    markdown = str(report.get("markdown", ""))
    return "AQuantLens Phase 1 sample report" in markdown


def sync_cleanup_predicate(
    *,
    keep_legacy_options_audit: bool,
    keep_pre_2026_06_19_sync: bool,
) -> tuple[str, tuple[object, ...]]:
    predicates = [
        "provider in (?, ?, ?)",
        "provider like ?",
    ]
    params: list[object] = ["sample", "fixture", "future", "unit-test-provider%"]
    if not keep_legacy_options_audit:
        predicates.append("(provider = ? and sync_type = ? and (target_symbol is null or target_expiry is null))")
        params.extend(["polygon", "options_chain"])
    if not keep_pre_2026_06_19_sync:
        predicates.append("started_at < ?")
        params.append("2026-06-19")
    return " or ".join(f"({predicate})" for predicate in predicates), tuple(params)


def apply_cleanup(
    connection: sqlite3.Connection,
    plan: dict[str, set[str]],
    sync_where: str,
    sync_params: tuple[object, ...],
) -> None:
    report_ids = plan["report_ids"]
    run_ids = plan["run_ids"]
    if report_ids:
        connection.execute(f"delete from analysis_reports where id in ({placeholders(report_ids)})", tuple(report_ids))
    if run_ids:
        connection.execute(f"delete from analysis_runs where id in ({placeholders(run_ids)})", tuple(run_ids))
    connection.execute(f"delete from provider_sync_runs where {sync_where}", sync_params)


def placeholders(values: set[str]) -> str:
    return ",".join("?" for _ in values)


if __name__ == "__main__":
    raise SystemExit(main())
