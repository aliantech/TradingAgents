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
    polygon_api_key = repository.get_raw_value("AQUANTLENS_POLYGON_API_KEY") or ""
    polygon_base_url = repository.get_raw_value("AQUANTLENS_POLYGON_BASE_URL") or ""
    return ProviderSettingsResponse(
        provider="polygon",
        polygon_configured=bool(polygon_api_key),
        polygon_base_url=polygon_base_url,
    )


@router.put("/provider", response_model=ProviderSettingsResponse)
def upsert_provider_settings(
    request: ProviderSettingsRequest,
    repository: SettingsRepository = Depends(get_settings_repository),
) -> ProviderSettingsResponse:
    provider = request.provider.lower()
    if provider != "polygon":
        raise HTTPException(status_code=400, detail=f"Unsupported provider: {request.provider}.")

    items: list[SettingWriteItem] = []
    if request.polygon_api_key is not None:
        items.append(
            SettingWriteItem(
                key="AQUANTLENS_POLYGON_API_KEY",
                value=request.polygon_api_key,
                category="api",
                is_secret=True,
            )
        )
    if request.polygon_base_url is not None:
        items.append(
            SettingWriteItem(
                key="AQUANTLENS_POLYGON_BASE_URL",
                value=request.polygon_base_url,
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
