from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel


class Quote(BaseModel):
    symbol: str
    name: str
    currency: Literal["KRW", "USD"]
    price: Decimal
    change: Decimal
    change_rate: Decimal
    market_open: bool
    delayed: bool = True
    as_of: datetime
