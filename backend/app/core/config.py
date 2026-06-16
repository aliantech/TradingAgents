from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    service_name: str = "AQuantLens API"
    database_url: str = "postgresql://aquser:aquantlens_dev_password@127.0.0.1:5432/aquantlens_us"
    redis_url: str = "redis://127.0.0.1:6379/0"

    model_config = SettingsConfigDict(env_prefix="AQUANTLENS_")


settings = Settings()
