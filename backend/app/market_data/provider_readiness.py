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
    if provider_name == "polygon":
        missing = []
        if not settings.polygon_api_key:
            missing.append("AQUANTLENS_POLYGON_API_KEY")
        if not settings.polygon_base_url:
            missing.append("AQUANTLENS_POLYGON_BASE_URL")
        return ProviderReadiness(
            provider="polygon",
            ready=not missing,
            missing=missing,
            message=(
                "Polygon provider is ready for a live smoke run."
                if not missing
                else "Polygon provider is missing required runtime configuration."
            ),
        )
    return ProviderReadiness(
        provider=provider_name,
        ready=False,
        missing=["AQUANTLENS_MARKET_DATA_PROVIDER"],
        message=f"Unsupported market data provider: {provider_name}.",
    )
