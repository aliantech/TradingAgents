from datetime import UTC, datetime
from typing import Any

from sqlalchemy.orm import Session

from app.core.config import Settings, settings
from app.db.models import AppSettingModel
from app.settings.repository import SettingsRepository

_RUNTIME_SETTING_FIELDS: dict[str, tuple[str, type]] = {
    "AQUANTLENS_SERVICE_NAME": ("service_name", str),
    "AQUANTLENS_DATABASE_URL": ("database_url", str),
    "AQUANTLENS_MARKET_DATA_PROVIDER": ("market_data_provider", str),
    "AQUANTLENS_POLYGON_API_KEY": ("polygon_api_key", str),
    "AQUANTLENS_POLYGON_BASE_URL": ("polygon_base_url", str),
    "AQUANTLENS_PROVIDER_MAX_RETRIES": ("provider_max_retries", int),
    "AQUANTLENS_PROVIDER_RETRY_BACKOFF_SECONDS": ("provider_retry_backoff_seconds", float),
    "AQUANTLENS_MANUAL_MARKET_SYNC_ENABLED": ("manual_market_sync_enabled", bool),
    "AQUANTLENS_PROVIDER_SYNC_STALE_AFTER_MINUTES": ("provider_sync_stale_after_minutes", int),
    "AQUANTLENS_PROVIDER_SYNC_FAILURE_RATE_THRESHOLD": ("provider_sync_failure_rate_threshold", float),
    "AQUANTLENS_SCHEDULER_TARGETS": ("scheduler_targets", str),
    "AQUANTLENS_SCHEDULER_INTERVAL_SECONDS": ("scheduler_interval_seconds", int),
    "AQUANTLENS_REALTIME_MARKET_PUBLISH_ENABLED": ("realtime_market_publish_enabled", bool),
    "AQUANTLENS_REALTIME_MARKET_TTL_SECONDS": ("realtime_market_ttl_seconds", int),
    "AQUANTLENS_REDIS_URL": ("redis_url", str),
    "AQUANTLENS_TRADINGAGENTS_RUNNER_MODE": ("tradingagents_runner_mode", str),
    "AQUANTLENS_TRADINGAGENTS_LLM_PROVIDER": ("tradingagents_llm_provider", str),
    "AQUANTLENS_TRADINGAGENTS_DEEP_THINK_LLM": ("tradingagents_deep_think_llm", str),
    "AQUANTLENS_TRADINGAGENTS_QUICK_THINK_LLM": ("tradingagents_quick_think_llm", str),
    "AQUANTLENS_TRADINGAGENTS_OUTPUT_LANGUAGE": ("tradingagents_output_language", str),
    "AQUANTLENS_TRADINGAGENTS_SELECTED_ANALYSTS": ("tradingagents_selected_analysts", str),
    "AQUANTLENS_TRADINGAGENTS_MAX_DEBATE_ROUNDS": ("tradingagents_max_debate_rounds", int),
    "AQUANTLENS_TRADINGAGENTS_MAX_RISK_DISCUSS_ROUNDS": ("tradingagents_max_risk_discuss_rounds", int),
}

STATIC_DEFAULT_DATABASE_SETTINGS: dict[str, tuple[str, str, bool]] = {
    "AQUANTLENS_SERVICE_NAME": ("AQuantLens API", "system", False),
    "AQUANTLENS_MARKET_DATA_PROVIDER": ("polygon", "api", False),
    "AQUANTLENS_POLYGON_API_KEY": ("", "api", True),
    "AQUANTLENS_POLYGON_BASE_URL": ("https://api.polygon.io", "api", False),
    "AQUANTLENS_PROVIDER_MAX_RETRIES": ("2", "data", False),
    "AQUANTLENS_PROVIDER_RETRY_BACKOFF_SECONDS": ("1.0", "data", False),
    "AQUANTLENS_MANUAL_MARKET_SYNC_ENABLED": ("true", "api", False),
    "AQUANTLENS_PROVIDER_SYNC_STALE_AFTER_MINUTES": ("1440", "data", False),
    "AQUANTLENS_PROVIDER_SYNC_FAILURE_RATE_THRESHOLD": ("0.5", "data", False),
    "AQUANTLENS_SCHEDULER_TARGETS": ("SPY:1d:2", "data", False),
    "AQUANTLENS_SCHEDULER_INTERVAL_SECONDS": ("300", "data", False),
    "AQUANTLENS_REALTIME_MARKET_PUBLISH_ENABLED": ("false", "system", False),
    "AQUANTLENS_REALTIME_MARKET_TTL_SECONDS": ("300", "system", False),
    "AQUANTLENS_REDIS_URL": ("redis://127.0.0.1:6379/0", "system", False),
    "AQUANTLENS_DATABASE_URL": ("sqlite:///./aquantlens_us.db", "system", False),
    "AQUANTLENS_TRADINGAGENTS_RUNNER_MODE": ("deterministic", "ai", False),
    "AQUANTLENS_TRADINGAGENTS_LLM_PROVIDER": ("openai", "ai", False),
    "AQUANTLENS_TRADINGAGENTS_DEEP_THINK_LLM": ("gpt-5.5", "ai", False),
    "AQUANTLENS_TRADINGAGENTS_QUICK_THINK_LLM": ("gpt-5.4-mini", "ai", False),
    "AQUANTLENS_TRADINGAGENTS_OUTPUT_LANGUAGE": ("Chinese", "ai", False),
    "AQUANTLENS_TRADINGAGENTS_SELECTED_ANALYSTS": ("market,news,fundamentals", "ai", False),
    "AQUANTLENS_TRADINGAGENTS_MAX_DEBATE_ROUNDS": ("1", "ai", False),
    "AQUANTLENS_TRADINGAGENTS_MAX_RISK_DISCUSS_ROUNDS": ("1", "ai", False),
    "VITE_API_BASE_URL": ("http://127.0.0.1:8022", "api", False),
}


def seed_default_database_settings(session: Session) -> None:
    first_bootstrap = session.query(AppSettingModel).count() == 0
    now = datetime.now(UTC)
    changed = False
    seed_values = _bootstrap_database_settings() if first_bootstrap else STATIC_DEFAULT_DATABASE_SETTINGS
    for key, (value, category, is_secret) in seed_values.items():
        if session.get(AppSettingModel, key) is not None:
            continue
        session.add(
            AppSettingModel(
                key=key,
                value=value,
                category=category,
                is_secret=is_secret,
                updated_at=now,
            )
        )
        changed = True
    if changed:
        session.commit()


def _bootstrap_database_settings() -> dict[str, tuple[str, str, bool]]:
    return {
        **STATIC_DEFAULT_DATABASE_SETTINGS,
        "AQUANTLENS_SERVICE_NAME": (settings.service_name, "system", False),
        "AQUANTLENS_MARKET_DATA_PROVIDER": (settings.market_data_provider, "api", False),
        "AQUANTLENS_POLYGON_API_KEY": (settings.polygon_api_key, "api", True),
        "AQUANTLENS_POLYGON_BASE_URL": (settings.polygon_base_url, "api", False),
        "AQUANTLENS_PROVIDER_MAX_RETRIES": (str(settings.provider_max_retries), "data", False),
        "AQUANTLENS_PROVIDER_RETRY_BACKOFF_SECONDS": (str(settings.provider_retry_backoff_seconds), "data", False),
        "AQUANTLENS_MANUAL_MARKET_SYNC_ENABLED": (str(settings.manual_market_sync_enabled).lower(), "api", False),
        "AQUANTLENS_PROVIDER_SYNC_STALE_AFTER_MINUTES": (str(settings.provider_sync_stale_after_minutes), "data", False),
        "AQUANTLENS_PROVIDER_SYNC_FAILURE_RATE_THRESHOLD": (
            str(settings.provider_sync_failure_rate_threshold),
            "data",
            False,
        ),
        "AQUANTLENS_SCHEDULER_TARGETS": (settings.scheduler_targets, "data", False),
        "AQUANTLENS_SCHEDULER_INTERVAL_SECONDS": (str(settings.scheduler_interval_seconds), "data", False),
        "AQUANTLENS_REALTIME_MARKET_PUBLISH_ENABLED": (
            str(settings.realtime_market_publish_enabled).lower(),
            "system",
            False,
        ),
        "AQUANTLENS_REALTIME_MARKET_TTL_SECONDS": (str(settings.realtime_market_ttl_seconds), "system", False),
        "AQUANTLENS_REDIS_URL": (settings.redis_url, "system", False),
        "AQUANTLENS_DATABASE_URL": (settings.database_url, "system", False),
        "AQUANTLENS_TRADINGAGENTS_RUNNER_MODE": (settings.tradingagents_runner_mode, "ai", False),
        "AQUANTLENS_TRADINGAGENTS_LLM_PROVIDER": (settings.tradingagents_llm_provider, "ai", False),
        "AQUANTLENS_TRADINGAGENTS_DEEP_THINK_LLM": (settings.tradingagents_deep_think_llm, "ai", False),
        "AQUANTLENS_TRADINGAGENTS_QUICK_THINK_LLM": (settings.tradingagents_quick_think_llm, "ai", False),
        "AQUANTLENS_TRADINGAGENTS_OUTPUT_LANGUAGE": (settings.tradingagents_output_language, "ai", False),
        "AQUANTLENS_TRADINGAGENTS_SELECTED_ANALYSTS": (settings.tradingagents_selected_analysts, "ai", False),
        "AQUANTLENS_TRADINGAGENTS_MAX_DEBATE_ROUNDS": (str(settings.tradingagents_max_debate_rounds), "ai", False),
        "AQUANTLENS_TRADINGAGENTS_MAX_RISK_DISCUSS_ROUNDS": (
            str(settings.tradingagents_max_risk_discuss_rounds),
            "ai",
            False,
        ),
    }


def resolve_runtime_settings(session: Session) -> Settings:
    seed_default_database_settings(session)
    repository = SettingsRepository(session)
    overrides: dict[str, Any] = {}
    for key, (field_name, field_type) in _RUNTIME_SETTING_FIELDS.items():
        raw_value = repository.get_raw_value(key)
        if raw_value is None:
            continue
        overrides[field_name] = _coerce(raw_value, field_type)
    return settings.model_copy(update=overrides)


def _coerce(value: str, field_type: type) -> Any:
    if field_type is bool:
        return value.strip().lower() in {"1", "true", "yes", "on"}
    if field_type is int:
        return int(value)
    if field_type is float:
        return float(value)
    return value
