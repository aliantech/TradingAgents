from dataclasses import dataclass
from datetime import date, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.db.models import OptionContractModel, OptionSnapshotModel, utc_now


@dataclass(frozen=True)
class OptionContractRecord:
    option_symbol: str
    underlying_symbol: str
    expiry: date
    strike: float
    option_type: str
    exercise_style: str | None
    expiration_type: str | None
    source: str
    id: UUID | None = None


@dataclass(frozen=True)
class OptionSnapshotRecord:
    option_symbol: str
    underlying_symbol: str
    timestamp: datetime
    bid: float | None
    ask: float | None
    last: float | None
    volume: int
    open_interest: int | None
    implied_volatility: float | None
    delta: float | None
    gamma: float | None
    theta: float | None
    vega: float | None
    source: str
    id: UUID | None = None


class OptionRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def upsert_contract(self, record: OptionContractRecord) -> OptionContractRecord:
        option_symbol = record.option_symbol.upper()
        underlying_symbol = record.underlying_symbol.upper()
        source = record.source.lower()
        model = self.session.scalar(
            select(OptionContractModel).where(
                OptionContractModel.option_symbol == option_symbol,
                OptionContractModel.source == source,
            )
        )
        if model is None:
            model = OptionContractModel(
                option_symbol=option_symbol,
                underlying_symbol=underlying_symbol,
                expiry=record.expiry,
                strike=record.strike,
                option_type=record.option_type.lower(),
                exercise_style=record.exercise_style,
                expiration_type=record.expiration_type,
                source=source,
            )
            self.session.add(model)
        else:
            model.underlying_symbol = underlying_symbol
            model.expiry = record.expiry
            model.strike = record.strike
            model.option_type = record.option_type.lower()
            model.exercise_style = record.exercise_style
            model.expiration_type = record.expiration_type
            model.updated_at = utc_now()
        self.session.commit()
        self.session.refresh(model)
        return self._contract_to_record(model)

    def list_contracts(
        self,
        *,
        underlying_symbol: str,
        expiry: date | None = None,
    ) -> list[OptionContractRecord]:
        statement = select(OptionContractModel).where(
            OptionContractModel.underlying_symbol == underlying_symbol.upper()
        )
        if expiry is not None:
            statement = statement.where(OptionContractModel.expiry == expiry)
        statement = statement.order_by(
            OptionContractModel.expiry.asc(),
            OptionContractModel.strike.asc(),
            OptionContractModel.option_type.asc(),
        )
        return [self._contract_to_record(model) for model in self.session.scalars(statement).all()]

    def upsert_snapshot(self, record: OptionSnapshotRecord) -> OptionSnapshotRecord:
        option_symbol = record.option_symbol.upper()
        source = record.source.lower()
        contract = self.session.scalar(
            select(OptionContractModel).where(
                OptionContractModel.option_symbol == option_symbol,
                OptionContractModel.source == source,
            )
        )
        if contract is None:
            raise ValueError(f"Option contract not found for {option_symbol} from {source}.")
        model = self.session.scalar(
            select(OptionSnapshotModel).where(
                OptionSnapshotModel.option_contract_id == contract.id,
                OptionSnapshotModel.timestamp == record.timestamp,
                OptionSnapshotModel.source == source,
            )
        )
        if model is None:
            model = OptionSnapshotModel(
                option_contract_id=contract.id,
                underlying_symbol=record.underlying_symbol.upper(),
                timestamp=record.timestamp,
                bid=record.bid,
                ask=record.ask,
                last=record.last,
                volume=record.volume,
                open_interest=record.open_interest,
                implied_volatility=record.implied_volatility,
                delta=record.delta,
                gamma=record.gamma,
                theta=record.theta,
                vega=record.vega,
                source=source,
            )
            self.session.add(model)
        else:
            model.underlying_symbol = record.underlying_symbol.upper()
            model.bid = record.bid
            model.ask = record.ask
            model.last = record.last
            model.volume = record.volume
            model.open_interest = record.open_interest
            model.implied_volatility = record.implied_volatility
            model.delta = record.delta
            model.gamma = record.gamma
            model.theta = record.theta
            model.vega = record.vega
        self.session.commit()
        self.session.refresh(model, attribute_names=["contract"])
        return self._snapshot_to_record(model)

    def list_chain_snapshots(
        self,
        *,
        underlying_symbol: str,
        expiry: date,
    ) -> list[OptionSnapshotRecord]:
        statement = (
            select(OptionSnapshotModel)
            .join(OptionSnapshotModel.contract)
            .options(joinedload(OptionSnapshotModel.contract))
            .where(
                OptionSnapshotModel.underlying_symbol == underlying_symbol.upper(),
                OptionContractModel.expiry == expiry,
            )
            .order_by(
                OptionContractModel.strike.asc(),
                OptionContractModel.option_type.asc(),
                OptionSnapshotModel.timestamp.desc(),
            )
        )
        return [self._snapshot_to_record(model) for model in self.session.scalars(statement).all()]

    def _contract_to_record(self, model: OptionContractModel) -> OptionContractRecord:
        return OptionContractRecord(
            id=model.id,
            option_symbol=model.option_symbol,
            underlying_symbol=model.underlying_symbol,
            expiry=model.expiry,
            strike=model.strike,
            option_type=model.option_type,
            exercise_style=model.exercise_style,
            expiration_type=model.expiration_type,
            source=model.source,
        )

    def _snapshot_to_record(self, model: OptionSnapshotModel) -> OptionSnapshotRecord:
        return OptionSnapshotRecord(
            id=model.id,
            option_symbol=model.contract.option_symbol,
            underlying_symbol=model.underlying_symbol,
            timestamp=model.timestamp,
            bid=model.bid,
            ask=model.ask,
            last=model.last,
            volume=model.volume,
            open_interest=model.open_interest,
            implied_volatility=model.implied_volatility,
            delta=model.delta,
            gamma=model.gamma,
            theta=model.theta,
            vega=model.vega,
            source=model.source,
        )
