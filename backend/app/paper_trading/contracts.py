from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StrictContract(BaseModel):
    model_config = ConfigDict(extra="forbid")


class PaperAccountStatus(StrEnum):
    ACTIVE = "active"
    PAUSED = "paused"
    ARCHIVED = "archived"


class OrderSource(StrEnum):
    HUMAN = "human"
    AGENT = "agent"
    SYSTEM = "system"


class AssetClass(StrEnum):
    EQUITY = "equity"
    ETF = "etf"
    INDEX_OPTION = "index-option"
    EQUITY_OPTION = "equity-option"


class OrderSide(StrEnum):
    BUY = "buy"
    SELL = "sell"


class OrderType(StrEnum):
    MARKET = "market"
    LIMIT = "limit"


class TimeInForce(StrEnum):
    DAY = "day"
    GTC = "gtc"


class OrderIntentStatus(StrEnum):
    DRAFT = "draft"
    RISK_REJECTED = "risk_rejected"
    AWAITING_REVIEW = "awaiting_review"
    APPROVED_FOR_PAPER = "approved_for_paper"
    PAPER_SUBMITTED = "paper_submitted"
    PAPER_FILLED = "paper_filled"
    PAPER_CANCELLED = "paper_cancelled"


class RiskDecisionResult(StrEnum):
    PASS = "pass"
    REJECT = "reject"


class AuditResourceType(StrEnum):
    ORDER_INTENT = "order_intent"
    RISK_DECISION = "risk_decision"
    PAPER_FILL = "paper_fill"
    PAPER_POSITION = "paper_position"


class AuditOutcome(StrEnum):
    SUCCESS = "success"
    DENIED = "denied"
    ERROR = "error"


class PaperAccount(StrictContract):
    account_id: UUID
    name: str = Field(min_length=1, max_length=120)
    base_currency: str = Field(default="USD", min_length=3, max_length=3)
    starting_cash: float = Field(gt=0, allow_inf_nan=False)
    current_cash: float = Field(allow_inf_nan=False)
    status: PaperAccountStatus
    created_at: datetime


class PaperOrderIntent(StrictContract):
    intent_id: UUID
    account_id: UUID
    source: OrderSource
    source_reference_id: UUID
    symbol: str = Field(min_length=1, max_length=64)
    asset_class: AssetClass
    side: OrderSide
    quantity: float = Field(gt=0, allow_inf_nan=False)
    order_type: OrderType
    limit_price: float | None = Field(default=None, gt=0, allow_inf_nan=False)
    time_in_force: TimeInForce
    status: OrderIntentStatus
    idempotency_key: str = Field(min_length=8, max_length=160)
    created_at: datetime

    @model_validator(mode="after")
    def validate_limit_price_for_order_type(self) -> "PaperOrderIntent":
        if self.order_type == OrderType.LIMIT and self.limit_price is None:
            raise ValueError("limit_price is required for limit orders")
        if self.order_type == OrderType.MARKET and self.limit_price is not None:
            raise ValueError("limit_price is not allowed for market orders")
        return self


class RiskDecision(StrictContract):
    decision_id: UUID
    intent_id: UUID
    result: RiskDecisionResult
    reason_codes: list[str] = Field(min_length=1)
    explanation: str = Field(min_length=1, max_length=500)
    estimated_notional: float = Field(ge=0, allow_inf_nan=False)
    created_at: datetime


class PaperFill(StrictContract):
    fill_id: UUID
    intent_id: UUID
    account_id: UUID
    symbol: str = Field(min_length=1, max_length=64)
    asset_class: AssetClass
    side: OrderSide
    quantity: float = Field(gt=0, allow_inf_nan=False)
    fill_price: float = Field(gt=0, allow_inf_nan=False)
    filled_at: datetime


class PaperPosition(StrictContract):
    position_id: UUID
    account_id: UUID
    symbol: str = Field(min_length=1, max_length=64)
    asset_class: AssetClass
    quantity: float = Field(allow_inf_nan=False)
    average_price: float = Field(ge=0, allow_inf_nan=False)
    updated_at: datetime


class PaperAuditEvent(StrictContract):
    event_id: UUID
    actor_type: str = Field(min_length=1, max_length=64)
    resource_type: AuditResourceType
    resource_id: UUID
    action: str = Field(min_length=1, max_length=120)
    outcome: AuditOutcome
    reason_code: str = Field(min_length=1, max_length=120)
    message: str = Field(min_length=1, max_length=500)
    created_at: datetime
