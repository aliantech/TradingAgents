from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    service_name: str = "AQuantLens API"
    database_url: str = "sqlite:///./aquantlens_us.db"
    redis_url: str = "redis://127.0.0.1:6379/0"
    market_data_provider: str = "sample"
    polygon_api_key: str = ""
    polygon_base_url: str = "https://api.polygon.io"
    provider_max_retries: int = 2
    provider_retry_backoff_seconds: float = 1.0
    manual_market_sync_enabled: bool = True
    provider_sync_stale_after_minutes: int = 1440
    provider_sync_failure_rate_threshold: float = 0.5
    realtime_market_publish_enabled: bool = False
    realtime_market_ttl_seconds: int = 300

    model_config = SettingsConfigDict(env_prefix="AQUANTLENS_")


settings = Settings()
