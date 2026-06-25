from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db_session
from app.settings.repository import SettingsRepository
from app.settings.schemas import (
    ProviderSettingsRequest,
    ProviderSettingsResponse,
    SettingWriteItem,
    SettingsResponse,
    SettingsUpsertRequest,
)

router = APIRouter(prefix="/api/settings", tags=["settings"])


def get_settings_repository(session: Session = Depends(get_db_session)) -> SettingsRepository:
    return SettingsRepository(session)


@router.get("", response_model=SettingsResponse)
def list_settings(repository: SettingsRepository = Depends(get_settings_repository)) -> SettingsResponse:
    return SettingsResponse(items=repository.list_settings())


@router.get("/provider", response_model=ProviderSettingsResponse)
def get_provider_settings(
    repository: SettingsRepository = Depends(get_settings_repository),
) -> ProviderSettingsResponse:
    hub_base_url = repository.get_raw_value("AQUANTLENS_FINANCE_DATA_HUB_BASE_URL") or ""
    return ProviderSettingsResponse(
        provider="finance_data_hub",
        finance_data_hub_base_url=hub_base_url,
    )


@router.put("/provider", response_model=ProviderSettingsResponse)
def upsert_provider_settings(
    request: ProviderSettingsRequest,
    repository: SettingsRepository = Depends(get_settings_repository),
) -> ProviderSettingsResponse:
    provider = request.provider.lower()
    if provider != "finance_data_hub":
        raise HTTPException(status_code=400, detail=f"Unsupported provider: {request.provider}.")

    items: list[SettingWriteItem] = []
    if request.finance_data_hub_base_url is not None:
        items.append(
            SettingWriteItem(
                key="AQUANTLENS_FINANCE_DATA_HUB_BASE_URL",
                value=request.finance_data_hub_base_url,
                category="api",
                is_secret=False,
            )
        )
    if items:
        repository.upsert_many(items)

    return get_provider_settings(repository)


@router.put("", response_model=SettingsResponse)
def upsert_settings(
    request: SettingsUpsertRequest,
    repository: SettingsRepository = Depends(get_settings_repository),
) -> SettingsResponse:
    return SettingsResponse(items=repository.upsert_many(request.items))
