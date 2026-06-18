from app.db.models import AppSettingModel
from app.db.session import SessionLocal, initialize_database


class RuntimeConfig:
    def clear(self) -> None:
        initialize_database()
        session = SessionLocal()
        try:
            polygon_key = session.get(AppSettingModel, "AQUANTLENS_POLYGON_API_KEY")
            if polygon_key is not None:
                polygon_key.value = ""
                session.commit()
        finally:
            session.close()


runtime_config = RuntimeConfig()
