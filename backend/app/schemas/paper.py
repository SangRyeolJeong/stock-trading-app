from datetime import datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

Currency = Literal["KRW", "USD"]
OrderSide = Literal["buy", "sell"]


class PaperOrderRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    symbol: str = Field(min_length=1, max_length=12)
    side: OrderSide
    order_type: Literal["market", "limit"] = "market"
    quantity: Decimal = Field(gt=0, le=Decimal("100000"))
    limit_price: Decimal | None = Field(default=None, gt=0)
    idempotency_key: str = Field(min_length=8, max_length=128)

    @model_validator(mode="after")
    def normalize_and_validate(self) -> "PaperOrderRequest":
        self.symbol = self.symbol.strip().upper()
        if self.order_type == "limit" and self.limit_price is None:
            raise ValueError("지정가 주문에는 가격이 필요합니다.")
        return self


class PaperOrder(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    account_id: str
    idempotency_key: str
    status: Literal["accepted", "filled", "rejected", "cancelled"]
    symbol: str
    name: str
    currency: Currency
    side: OrderSide
    order_type: Literal["market", "limit"]
    quantity: Decimal
    limit_price: Decimal | None
    filled_price: Decimal | None
    gross_amount: Decimal | None
    fee: Decimal | None
    realized_pnl: Decimal | None
    created_at: datetime


class PaperOrderStatusEvent(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    order_id: UUID
    sequence: int
    previous_status: Literal["accepted", "filled", "rejected", "cancelled"] | None
    new_status: Literal["accepted", "filled", "rejected", "cancelled"]
    reason: str
    created_at: datetime


class CashBalance(BaseModel):
    currency: Currency
    amount: Decimal


class PaperAccount(BaseModel):
    id: str
    name: str
    base_currency: Currency
    cash_balances: list[CashBalance]
    created_at: datetime


class Position(BaseModel):
    id: UUID
    account_id: str
    symbol: str
    name: str
    currency: Currency
    quantity: Decimal
    average_cost: Decimal
    realized_pnl: Decimal
    current_price: Decimal | None = None
    market_value: Decimal | None = None
    unrealized_pnl: Decimal | None = None
    return_rate: Decimal | None = None
    updated_at: datetime


class PortfolioCurrencySummary(BaseModel):
    currency: Currency
    cash: Decimal
    positions_value: Decimal
    total_value: Decimal
    unrealized_pnl: Decimal
    realized_pnl: Decimal


class PortfolioSummary(BaseModel):
    account_id: str
    currencies: list[PortfolioCurrencySummary]
    positions: list[Position]
    as_of: datetime
