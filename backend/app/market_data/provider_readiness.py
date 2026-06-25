from dataclasses import dataclass

from app.core.config import Settings


@dataclass(frozen=True)
class ProviderReadiness:
    provider: str
    ready: bool
    missing: list[str]
    message: str


def check_market_data_provider_readiness(settings: Settings, provider: str | None = None) -> ProviderReadiness:
    provider_name = (provider or settings.market_data_provider).lower().strip()
    if provider_name == "finance_data_hub":
        missing = []
        if not settings.finance_data_hub_base_url:
            missing.append("AQUANTLENS_FINANCE_DATA_HUB_BASE_URL")
        return ProviderReadiness(
            provider="finance_data_hub",
            ready=not missing,
            missing=missing,
            message=(
                "Finance Data Hub is configured for read-only market data access."
                if not missing
                else "Finance Data Hub is missing required runtime configuration."
            ),
        )
    return ProviderReadiness(
        provider=provider_name,
        ready=False,
        missing=["AQUANTLENS_MARKET_DATA_PROVIDER"],
        message=f"Unsupported market data provider: {provider_name}.",
    )
