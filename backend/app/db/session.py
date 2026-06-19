from collections.abc import Generator

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings
from app.db.base import Base
from app.db import models  # noqa: F401

connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
_initialized = False


def initialize_database() -> None:
    global _initialized
    if _initialized:
        return
    Base.metadata.create_all(bind=engine)
    _ensure_analysis_run_columns()
    _ensure_provider_sync_run_columns()
    _seed_default_settings()
    _initialized = True


def _ensure_analysis_run_columns() -> None:
    inspector = inspect(engine)
    if "analysis_runs" not in inspector.get_table_names():
        return
    columns = {column["name"] for column in inspector.get_columns("analysis_runs")}
    if "analyst_set" in columns:
        needs_analyst_set = False
    else:
        needs_analyst_set = True
    needs_research_template = "research_template" not in columns
    if not needs_analyst_set and not needs_research_template:
        return
    with engine.begin() as connection:
        if needs_analyst_set:
            connection.execute(
                text("ALTER TABLE analysis_runs ADD COLUMN analyst_set VARCHAR(64) NOT NULL DEFAULT 'macro-options'")
            )
        if needs_research_template:
            connection.execute(
                text("ALTER TABLE analysis_runs ADD COLUMN research_template VARCHAR(64) NOT NULL DEFAULT 'general'")
            )


def _ensure_provider_sync_run_columns() -> None:
    inspector = inspect(engine)
    if "provider_sync_runs" not in inspector.get_table_names():
        return
    columns = {column["name"] for column in inspector.get_columns("provider_sync_runs")}
    needs_target_symbol = "target_symbol" not in columns
    needs_target_expiry = "target_expiry" not in columns
    if not needs_target_symbol and not needs_target_expiry:
        return
    with engine.begin() as connection:
        if needs_target_symbol:
            connection.execute(text("ALTER TABLE provider_sync_runs ADD COLUMN target_symbol VARCHAR(64)"))
        if needs_target_expiry:
            connection.execute(text("ALTER TABLE provider_sync_runs ADD COLUMN target_expiry DATE"))


def _seed_default_settings() -> None:
    from app.settings.runtime import seed_default_database_settings

    session = SessionLocal()
    try:
        seed_default_database_settings(session)
    finally:
        session.close()


def get_db_session() -> Generator[Session, None, None]:
    initialize_database()
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
