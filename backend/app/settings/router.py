from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.core.config import settings
from app.runtime_config import runtime_config

router = APIRouter(prefix="/api/settings", tags=["settings"])


class ProviderSettingsRequest(BaseModel):
    provider: str = Field(default="polygon", min_length=1, max_length=64)
    polygon_api_key: str | None = Field(default=None, min_length=1)
    polygon_base_url: str | None = Field(default=None, min_length=1, max_length=256)


class ProviderSettingsResponse(BaseModel):
    provider: str
    polygon_configured: bool
    polygon_base_url: str
    message: str


@router.get("/provider", response_model=ProviderSettingsResponse)
def get_provider_settings() -> ProviderSettingsResponse:
    snapshot = runtime_config.snapshot(settings)
    return ProviderSettingsResponse(
        provider=snapshot.provider,
        polygon_configured=snapshot.polygon_configured,
        polygon_base_url=snapshot.polygon_base_url,
        message="Runtime provider settings loaded.",
    )


@router.put("/provider", response_model=ProviderSettingsResponse)
def update_provider_settings(request: ProviderSettingsRequest) -> ProviderSettingsResponse:
    if request.provider.lower() != "polygon":
        raise HTTPException(status_code=400, detail=f"Unsupported provider: {request.provider}.")
    snapshot = runtime_config.update_polygon(
        api_key=request.polygon_api_key,
        base_url=request.polygon_base_url,
    )
    return ProviderSettingsResponse(
        provider=snapshot.provider,
        polygon_configured=snapshot.polygon_configured,
        polygon_base_url=snapshot.polygon_base_url,
        message="Polygon runtime settings updated for this backend process.",
    )
