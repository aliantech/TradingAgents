from datetime import UTC, date, datetime
from uuid import UUID, uuid4

from sqlalchemy import BigInteger, Date, DateTime, Float, ForeignKey, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def utc_now() -> datetime:
    return datetime.now(UTC)


class AnalysisRunModel(Base):
    __tablename__ = "analysis_runs"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    symbol: Mapped[str] = mapped_column(String(64), index=True)
    asset_type: Mapped[str] = mapped_column(String(32))
    analysis_date: Mapped[date] = mapped_column(Date)
    language: Mapped[str] = mapped_column(String(8), default="zh")
    llm_provider: Mapped[str] = mapped_column(String(64))
    model: Mapped[str] = mapped_column(String(128))
    depth: Mapped[str] = mapped_column(String(32))
    analyst_set: Mapped[str] = mapped_column(String(64), default="macro-options")
    status: Mapped[str] = mapped_column(String(32))
    progress: Mapped[list[dict]] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    report: Mapped["AnalysisReportModel | None"] = relationship(
        back_populates="run",
        cascade="all, delete-orphan",
        uselist=False,
    )


class AnalysisReportModel(Base):
    __tablename__ = "analysis_reports"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    analysis_run_id: Mapped[UUID] = mapped_column(ForeignKey("analysis_runs.id"), index=True)
    symbol: Mapped[str] = mapped_column(String(64), index=True)
    language: Mapped[str] = mapped_column(String(8), default="zh")
    markdown: Mapped[str] = mapped_column(Text)
    report_json: Mapped[dict] = mapped_column(JSON)
    confidence: Mapped[float] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    run: Mapped[AnalysisRunModel] = relationship(back_populates="report")


class InstrumentModel(Base):
    __tablename__ = "instruments"
    __table_args__ = (UniqueConstraint("symbol", "asset_type", "exchange", name="uq_instruments_identity"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    symbol: Mapped[str] = mapped_column(String(64), index=True)
    asset_type: Mapped[str] = mapped_column(String(32))
    exchange: Mapped[str] = mapped_column(String(64))
    currency: Mapped[str] = mapped_column(String(8), default="USD")
    timezone: Mapped[str] = mapped_column(String(64), default="America/New_York")
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    source: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    bars: Mapped[list["MarketBarModel"]] = relationship(back_populates="instrument")


class MarketBarModel(Base):
    __tablename__ = "market_bars"

    instrument_id: Mapped[UUID] = mapped_column(ForeignKey("instruments.id"), primary_key=True)
    timeframe: Mapped[str] = mapped_column(String(16), primary_key=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), primary_key=True)
    source: Mapped[str] = mapped_column(String(64), primary_key=True)
    open: Mapped[float] = mapped_column(Float)
    high: Mapped[float] = mapped_column(Float)
    low: Mapped[float] = mapped_column(Float)
    close: Mapped[float] = mapped_column(Float)
    volume: Mapped[int] = mapped_column(BigInteger, default=0)
    inserted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    instrument: Mapped[InstrumentModel] = relationship(back_populates="bars")


class ProviderSyncRunModel(Base):
    __tablename__ = "provider_sync_runs"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    provider: Mapped[str] = mapped_column(String(64), index=True)
    sync_type: Mapped[str] = mapped_column(String(64), index=True)
    status: Mapped[str] = mapped_column(String(32), index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    rows_written: Mapped[int] = mapped_column(default=0)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)


class AppSettingModel(Base):
    __tablename__ = "app_settings"

    key: Mapped[str] = mapped_column(String(255), primary_key=True)
    value: Mapped[str] = mapped_column(Text)
    category: Mapped[str] = mapped_column(String(64), index=True)
    is_secret: Mapped[bool] = mapped_column(default=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class OptionContractModel(Base):
    __tablename__ = "option_contracts"
    __table_args__ = (
        UniqueConstraint("option_symbol", "source", name="uq_option_contracts_symbol_source"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    option_symbol: Mapped[str] = mapped_column(String(128), index=True)
    underlying_symbol: Mapped[str] = mapped_column(String(64), index=True)
    expiry: Mapped[date] = mapped_column(Date, index=True)
    strike: Mapped[float] = mapped_column(Float, index=True)
    option_type: Mapped[str] = mapped_column(String(8), index=True)
    exercise_style: Mapped[str | None] = mapped_column(String(32), nullable=True)
    expiration_type: Mapped[str | None] = mapped_column(String(32), nullable=True)
    source: Mapped[str] = mapped_column(String(64), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    snapshots: Mapped[list["OptionSnapshotModel"]] = relationship(back_populates="contract")


class OptionSnapshotModel(Base):
    __tablename__ = "option_snapshots"
    __table_args__ = (
        UniqueConstraint(
            "option_contract_id",
            "timestamp",
            "source",
            name="uq_option_snapshots_contract_time_source",
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    option_contract_id: Mapped[UUID] = mapped_column(ForeignKey("option_contracts.id"), index=True)
    underlying_symbol: Mapped[str] = mapped_column(String(64), index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    bid: Mapped[float | None] = mapped_column(Float, nullable=True)
    ask: Mapped[float | None] = mapped_column(Float, nullable=True)
    last: Mapped[float | None] = mapped_column(Float, nullable=True)
    volume: Mapped[int] = mapped_column(BigInteger, default=0)
    open_interest: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    implied_volatility: Mapped[float | None] = mapped_column(Float, nullable=True)
    delta: Mapped[float | None] = mapped_column(Float, nullable=True)
    gamma: Mapped[float | None] = mapped_column(Float, nullable=True)
    theta: Mapped[float | None] = mapped_column(Float, nullable=True)
    vega: Mapped[float | None] = mapped_column(Float, nullable=True)
    source: Mapped[str] = mapped_column(String(64), index=True)
    inserted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    contract: Mapped[OptionContractModel] = relationship(back_populates="snapshots")
