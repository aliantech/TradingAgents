from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.db.models import AppSettingModel
from app.settings.schemas import SettingReadItem, SettingWriteItem


class SettingsRepository:
    def __init__(self, session: Session):
        self.session = session

    def list_settings(self) -> list[SettingReadItem]:
        settings = self.session.query(AppSettingModel).order_by(AppSettingModel.category, AppSettingModel.key).all()
        return [_to_read_item(setting) for setting in settings]

    def get_raw_value(self, key: str) -> str | None:
        setting = self.session.get(AppSettingModel, key)
        if setting is None:
            return None
        return setting.value

    def upsert_many(self, items: list[SettingWriteItem]) -> list[SettingReadItem]:
        now = datetime.now(UTC)
        for item in items:
            existing = self.session.get(AppSettingModel, item.key)
            if existing:
                existing.value = item.value
                existing.category = item.category
                existing.is_secret = item.is_secret
                existing.updated_at = now
                continue
            self.session.add(
                AppSettingModel(
                    key=item.key,
                    value=item.value,
                    category=item.category,
                    is_secret=item.is_secret,
                    updated_at=now,
                )
            )
        self.session.commit()
        return self.list_settings()


def _to_read_item(setting: AppSettingModel) -> SettingReadItem:
    return SettingReadItem(
        key=setting.key,
        value=None if setting.is_secret else setting.value,
        category=setting.category,
        is_secret=setting.is_secret,
        has_value=bool(setting.value),
        updated_at=setting.updated_at,
    )
