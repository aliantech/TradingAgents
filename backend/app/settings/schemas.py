from datetime import datetime

from pydantic import BaseModel, Field


class SettingWriteItem(BaseModel):
    key: str = Field(min_length=1, max_length=255)
    value: str = ""
    category: str = Field(default="general", min_length=1, max_length=64)
    is_secret: bool = False


class SettingsUpsertRequest(BaseModel):
    items: list[SettingWriteItem] = Field(default_factory=list)


class SettingReadItem(BaseModel):
    key: str
    value: str | None
    category: str
    is_secret: bool
    has_value: bool
    updated_at: datetime


class SettingsResponse(BaseModel):
    items: list[SettingReadItem]


class ProviderSettingsRequest(BaseModel):
    provider: str = Field(min_length=1, max_length=64)
    finance_data_hub_base_url: str | None = None


class ProviderSettingsResponse(BaseModel):
    provider: str
    finance_data_hub_base_url: str
