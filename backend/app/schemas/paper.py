from datetime import datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, model_validator


class PaperOrderRequest(BaseModel):
    symbol: str = Field(min_length=1, max_length=12)
    side: Literal["buy", "sell"]
    order_type: Literal["market", "limit"]
    quantity: int = Field(gt=0, le=100_000)
    limit_price: Decimal | None = Field(default=None, gt=0)
    account_id: str = "demo-account"
    idempotency_key: str = Field(min_length=8, max_length=128)

    @model_validator(mode="after")
    def validate_limit_price(self) -> "PaperOrderRequest":
        if self.order_type == "limit" and self.limit_price is None:
            raise ValueError("지정가 주문에는 가격이 필요합니다.")
        return self


class PaperOrder(BaseModel):
    id: UUID
    idempotency_key: str
    status: Literal["accepted", "filled", "rejected"]
    symbol: str
    side: Literal["buy", "sell"]
    quantity: int
    filled_price: Decimal
    created_at: datetime
