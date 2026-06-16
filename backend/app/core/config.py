from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    service_name: str = "AQuantLens API"
    database_url: str = "sqlite:///./aquantlens_us.db"
    redis_url: str = "redis://127.0.0.1:6379/0"

    model_config = SettingsConfigDict(env_prefix="AQUANTLENS_")


settings = Settings()
