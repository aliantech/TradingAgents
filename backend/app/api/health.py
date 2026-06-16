from fastapi import APIRouter

from app.core.config import settings

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health")
def health() -> dict[str, str]:
    return {"service": settings.service_name, "status": "ok"}
