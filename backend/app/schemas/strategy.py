from typing import Literal

from pydantic import BaseModel, Field


class StrategyRequest(BaseModel):
    goal: Literal["retirement", "lump_sum", "cashflow"] = "retirement"
    horizon_years: int = Field(default=30, ge=1, le=50)
    monthly_amount_krw: int = Field(default=500_000, ge=10_000)
    risk_profile: Literal["conservative", "balanced", "growth"] = "growth"


class StrategyResponse(BaseModel):
    title: str
    score: int
    allocation: dict[str, int]
    reason_codes: list[str]
    reasons: list[str]
    disclaimer: str
