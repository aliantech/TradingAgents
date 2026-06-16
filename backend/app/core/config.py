from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    service_name: str = "AQuantLens API"

    model_config = SettingsConfigDict(env_prefix="AQUANTLENS_")


settings = Settings()
