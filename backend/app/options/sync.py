from dataclasses import dataclass
from datetime import UTC, date, datetime

from app.market_data.sync_repository import ProviderSyncRepository
from app.options.polygon_provider import OptionChainProvider
from app.options.repository import OptionRepository


@dataclass(frozen=True)
class OptionChainSyncResult:
    provider: str
    underlying_symbol: str
    expiry: str
    status: str
    rows_written: int
    error_message: str | None = None


class OptionChainSyncService:
    def __init__(
        self,
        *,
        provider: OptionChainProvider,
        provider_name: str,
        option_repository: OptionRepository,
        sync_repository: ProviderSyncRepository,
    ) -> None:
        self.provider = provider
        self.provider_name = provider_name
        self.option_repository = option_repository
        self.sync_repository = sync_repository

    def sync_chain(
        self,
        *,
        underlying_symbol: str,
        expiry: date,
        limit: int,
    ) -> OptionChainSyncResult:
        normalized_underlying = underlying_symbol.upper()
        started_at = datetime.now(tz=UTC)
        rows_written = 0
        try:
            records = self.provider.fetch_chain_snapshot(normalized_underlying, expiry=expiry, limit=limit)
            for record in records:
                self.option_repository.upsert_contract(record.contract)
                self.option_repository.upsert_snapshot(record.snapshot)
            rows_written = len(records)
            status = "succeeded"
            error_message = None
        except Exception as exc:  # noqa: BLE001 - sync audit must capture provider/runtime failures.
            status = "failed"
            error_message = str(exc)
        self.sync_repository.record_run(
            provider=self.provider_name,
            sync_type="options_chain",
            status=status,
            started_at=started_at,
            finished_at=datetime.now(tz=UTC),
            rows_written=rows_written,
            error_message=error_message,
        )
        return OptionChainSyncResult(
            provider=self.provider_name,
            underlying_symbol=normalized_underlying,
            expiry=expiry.isoformat(),
            status=status,
            rows_written=rows_written,
            error_message=error_message,
        )
