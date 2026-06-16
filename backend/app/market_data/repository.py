from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import InstrumentModel, MarketBarModel
from app.market_data.schemas import MarketBar


class MarketDataRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def save_bars(
        self,
        bars: list[MarketBar],
        *,
        asset_type: str = "etf",
        exchange: str = "US",
    ) -> int:
        rows_written = 0
        for bar in bars:
            normalized_symbol = bar.symbol.upper()
            instrument = self._get_or_create_instrument(
                symbol=normalized_symbol,
                asset_type=asset_type,
                exchange=exchange,
                source=bar.source,
            )
            timestamp = _as_utc(bar.timestamp)
            model = self.session.get(
                MarketBarModel,
                {
                    "instrument_id": instrument.id,
                    "timeframe": bar.timeframe,
                    "timestamp": timestamp,
                    "source": bar.source,
                },
            )
            if model is None:
                model = MarketBarModel(
                    instrument_id=instrument.id,
                    timeframe=bar.timeframe,
                    timestamp=timestamp,
                    source=bar.source,
                )
                self.session.add(model)
            model.open = bar.open
            model.high = bar.high
            model.low = bar.low
            model.close = bar.close
            model.volume = bar.volume
            rows_written += 1
        self.session.commit()
        return rows_written

    def list_bars(self, *, symbol: str, timeframe: str, limit: int = 500) -> list[MarketBar]:
        normalized_symbol = symbol.upper()
        statement = (
            select(MarketBarModel)
            .join(InstrumentModel)
            .where(InstrumentModel.symbol == normalized_symbol, MarketBarModel.timeframe == timeframe)
            .order_by(MarketBarModel.timestamp.asc())
            .limit(limit)
        )
        models = self.session.scalars(statement).all()
        return [self._to_schema(model) for model in models]

    def _get_or_create_instrument(
        self,
        *,
        symbol: str,
        asset_type: str,
        exchange: str,
        source: str,
    ) -> InstrumentModel:
        statement = select(InstrumentModel).where(
            InstrumentModel.symbol == symbol,
            InstrumentModel.asset_type == asset_type,
            InstrumentModel.exchange == exchange,
        )
        model = self.session.scalar(statement)
        if model is not None:
            return model
        model = InstrumentModel(symbol=symbol, asset_type=asset_type, exchange=exchange, source=source)
        self.session.add(model)
        self.session.flush()
        return model

    def _to_schema(self, model: MarketBarModel) -> MarketBar:
        return MarketBar(
            symbol=model.instrument.symbol,
            timeframe=model.timeframe,
            timestamp=_as_utc(model.timestamp),
            open=model.open,
            high=model.high,
            low=model.low,
            close=model.close,
            volume=model.volume,
            source=model.source,
        )


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)
