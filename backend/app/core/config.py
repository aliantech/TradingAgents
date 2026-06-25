from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    service_name: str = "AQuantLens API"
    database_url: str = "sqlite:///./aquantlens_us.db"
    redis_url: str = "redis://127.0.0.1:6379/0"
    market_data_provider: str = "finance_data_hub"
    finance_data_hub_base_url: str = "http://127.0.0.1:4101"
    provider_sync_stale_after_minutes: int = 1440
    provider_sync_failure_rate_threshold: float = 0.5
    realtime_market_publish_enabled: bool = False
    realtime_market_ttl_seconds: int = 300
    tradingagents_runner_mode: str = "deterministic"
    tradingagents_llm_provider: str = "openai"
    tradingagents_deep_think_llm: str = "gpt-5.5"
    tradingagents_quick_think_llm: str = "gpt-5.4-mini"
    tradingagents_output_language: str = "Chinese"
    tradingagents_selected_analysts: str = "market,news,fundamentals"
    tradingagents_max_debate_rounds: int = 1
    tradingagents_max_risk_discuss_rounds: int = 1

    model_config = SettingsConfigDict(env_prefix="AQUANTLENS_")


settings = Settings()
