from app.db.session import SessionLocal, initialize_database


class RuntimeConfig:
    def clear(self) -> None:
        initialize_database()
        session = SessionLocal()
        try:
            session.commit()
        finally:
            session.close()


runtime_config = RuntimeConfig()
