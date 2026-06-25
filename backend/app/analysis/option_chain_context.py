from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.db.models import OptionContractModel, OptionSnapshotModel
from app.market_data.finance_data_hub import FinanceDataHubClient, FinanceDataHubError
from app.settings.runtime import resolve_runtime_settings


def build_option_chain_context(session: Session, *, symbol: str, analysis_date: date, limit: int = 3) -> str:
    normalized_symbol = symbol.upper()
    try:
        hub_context = _build_finance_data_hub_context(
            session,
            symbol=normalized_symbol,
            analysis_date=analysis_date,
            limit=limit,
        )
        if hub_context:
            return hub_context
    except FinanceDataHubError:
        pass

    expiry = session.scalar(
        select(OptionContractModel.expiry)
        .join(OptionContractModel.snapshots)
        .where(
            OptionContractModel.underlying_symbol == normalized_symbol,
            OptionContractModel.expiry >= analysis_date,
        )
        .order_by(OptionContractModel.expiry.asc())
        .limit(1)
    )
    if expiry is None:
        return ""

    models = session.scalars(
        select(OptionSnapshotModel)
        .join(OptionSnapshotModel.contract)
        .options(joinedload(OptionSnapshotModel.contract))
        .where(
            OptionSnapshotModel.underlying_symbol == normalized_symbol,
            OptionContractModel.expiry == expiry,
        )
        .order_by(OptionSnapshotModel.timestamp.desc())
    ).all()
    latest_by_contract: dict[str, OptionSnapshotModel] = {}
    for model in models:
        latest_by_contract.setdefault(model.contract.option_symbol, model)
    snapshots = list(latest_by_contract.values())
    if not snapshots:
        return ""

    calls = sum(1 for snapshot in snapshots if snapshot.contract.option_type == "call")
    puts = sum(1 for snapshot in snapshots if snapshot.contract.option_type == "put")
    total_volume = sum(snapshot.volume or 0 for snapshot in snapshots)
    total_open_interest = sum(snapshot.open_interest or 0 for snapshot in snapshots)
    latest_timestamp = max(snapshot.timestamp for snapshot in snapshots)
    top_open_interest = sorted(snapshots, key=lambda snapshot: snapshot.open_interest or 0, reverse=True)[:limit]
    top_gamma = sorted(snapshots, key=lambda snapshot: abs(snapshot.gamma or 0), reverse=True)[:limit]

    return "\n".join(
        [
            (
                f"逐合约期权链快照（持久化数据）：{normalized_symbol} 最近到期日 {expiry.isoformat()}，"
                f"最新快照时间 {latest_timestamp.isoformat()}，覆盖 {len(snapshots)} 个合约"
                f"（Call {calls} / Put {puts}），总成交量 {total_volume}，总 open interest {total_open_interest}。"
            ),
            "Open interest 集中合约：",
            *[_format_option_snapshot(snapshot) for snapshot in top_open_interest],
            "Gamma 敏感合约：",
            *[_format_option_snapshot(snapshot) for snapshot in top_gamma],
        ]
    )


def _build_finance_data_hub_context(session: Session, *, symbol: str, analysis_date: date, limit: int) -> str:
    runtime_settings = resolve_runtime_settings(session)
    rows = FinanceDataHubClient(runtime_settings.finance_data_hub_base_url).list_option_latest_quote_rows(
        underlying_symbol=symbol,
    )
    rows = _nearest_expiry_rows(rows, analysis_date)
    if not rows:
        return ""
    calls = sum(1 for row in rows if str(row.get("right") or row.get("contract_type")).lower() == "call")
    puts = sum(1 for row in rows if str(row.get("right") or row.get("contract_type")).lower() == "put")
    total_volume = sum(_int_value(row.get("volume")) for row in rows)
    total_open_interest = sum(_int_value(row.get("open_interest")) for row in rows)
    timestamps = [str(row.get("provider_timestamp") or row.get("timestamp")) for row in rows if row.get("provider_timestamp") or row.get("timestamp")]
    latest_timestamp = max(timestamps) if timestamps else "暂无"
    expiry = str(rows[0].get("expiration_date") or analysis_date.isoformat())
    top_open_interest = sorted(rows, key=lambda row: _int_value(row.get("open_interest")), reverse=True)[:limit]
    top_gamma = sorted(rows, key=lambda row: abs(_float_value(row.get("gamma"))), reverse=True)[:limit]
    return "\n".join(
        [
            (
                f"逐合约期权链快照（Finance Data Hub 只读数据）：{symbol} 到期日 {expiry}，"
                f"最新快照时间 {latest_timestamp}，覆盖 {len(rows)} 个合约"
                f"（Call {calls} / Put {puts}），总成交量 {total_volume}，总 open interest {total_open_interest}。"
            ),
            "Open interest 集中合约：",
            *[_format_hub_option_row(row) for row in top_open_interest],
            "Gamma 敏感合约：",
            *[_format_hub_option_row(row) for row in top_gamma],
        ]
    )


def _format_option_snapshot(snapshot: OptionSnapshotModel) -> str:
    contract = snapshot.contract
    return (
        f"- {contract.option_symbol} {contract.option_type} strike {contract.strike:g}: "
        f"bid {format_optional(snapshot.bid)}, ask {format_optional(snapshot.ask)}, "
        f"last {format_optional(snapshot.last)}, volume {snapshot.volume or 0}, "
        f"open interest {format_optional(snapshot.open_interest)}, IV {format_optional(snapshot.implied_volatility)}, "
        f"delta {format_optional(snapshot.delta)}, Gamma {format_optional(snapshot.gamma)}"
    )


def _format_hub_option_row(row: dict) -> str:
    option_symbol = row.get("provider_symbol") or row.get("occ_symbol") or row.get("option_symbol") or "UNKNOWN"
    option_type = row.get("right") or row.get("contract_type") or "unknown"
    return (
        f"- {option_symbol} {option_type} strike {row.get('strike', '暂无')}: "
        f"bid {format_optional(_optional_float(row.get('bid')))}, ask {format_optional(_optional_float(row.get('ask')))}, "
        f"last {format_optional(_optional_float(row.get('last') or row.get('mid')))}, volume {_int_value(row.get('volume'))}, "
        f"open interest {format_optional(_optional_int(row.get('open_interest')))}, "
        f"IV {format_optional(_optional_float(row.get('implied_volatility') or row.get('iv')))}, "
        f"delta {format_optional(_optional_float(row.get('delta')))}, Gamma {format_optional(_optional_float(row.get('gamma')))}"
    )


def format_optional(value: float | int | None) -> str:
    if value is None:
        return "暂无"
    if isinstance(value, float):
        return f"{value:.4g}"
    return str(value)


def _nearest_expiry_rows(rows: list[dict], analysis_date: date) -> list[dict]:
    candidates: dict[date, list[dict]] = {}
    for row in rows:
        raw_expiry = row.get("expiration_date") or row.get("expiry")
        if raw_expiry is None:
            continue
        expiry = date.fromisoformat(str(raw_expiry)[:10])
        if expiry >= analysis_date:
            candidates.setdefault(expiry, []).append(row)
    if not candidates:
        return []
    return candidates[min(candidates)]


def _optional_float(value: object) -> float | None:
    if value in (None, ""):
        return None
    return float(value)


def _optional_int(value: object) -> int | None:
    if value in (None, ""):
        return None
    return int(value)


def _float_value(value: object) -> float:
    return _optional_float(value) or 0.0


def _int_value(value: object) -> int:
    return _optional_int(value) or 0
