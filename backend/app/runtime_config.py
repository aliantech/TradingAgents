from dataclasses import dataclass
from threading import RLock

from app.core.config import Settings


@dataclass(frozen=True)
class RuntimeProviderSnapshot:
    provider: str
    polygon_configured: bool
    polygon_base_url: str


class RuntimeConfig:
    def __init__(self) -> None:
        self._lock = RLock()
        self._polygon_api_key = ""
        self._polygon_base_url = ""

    def update_polygon(self, *, api_key: str | None = None, base_url: str | None = None) -> RuntimeProviderSnapshot:
        with self._lock:
            if api_key is not None:
                self._polygon_api_key = api_key.strip()
            if base_url is not None:
                self._polygon_base_url = base_url.strip()
            return self.snapshot()

    def snapshot(self, settings: Settings | None = None) -> RuntimeProviderSnapshot:
        with self._lock:
            base_url = self._polygon_base_url or (settings.polygon_base_url if settings else "")
            configured = bool(self._polygon_api_key or (settings.polygon_api_key if settings else ""))
            return RuntimeProviderSnapshot(
                provider="polygon",
                polygon_configured=configured,
                polygon_base_url=base_url,
            )

    def polygon_api_key(self, settings: Settings) -> str:
        with self._lock:
            return self._polygon_api_key or settings.polygon_api_key

    def polygon_base_url(self, settings: Settings) -> str:
        with self._lock:
            return self._polygon_base_url or settings.polygon_base_url

    def clear(self) -> None:
        with self._lock:
            self._polygon_api_key = ""
            self._polygon_base_url = ""


runtime_config = RuntimeConfig()
