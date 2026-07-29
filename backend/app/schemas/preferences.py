from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

StrategyGoal = Literal["retirement", "lump_sum", "cashflow"]
RiskProfile = Literal["conservative", "balanced", "growth"]


class UserPreferencesPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    display_name: str = Field(min_length=1, max_length=20)
    annual_salary_krw: int = Field(ge=0, le=1_000_000_000)
    monthly_investment_krw: int = Field(ge=10_000, le=100_000_000)
    investment_years: int = Field(ge=3, le=40)
    annual_return_rate_pct: float = Field(ge=0, le=30)
    withdrawal_age: int = Field(ge=55, le=100)
    strategy_goal: StrategyGoal
    risk_profile: RiskProfile
    liquidity_preference: bool
    fee_sensitivity: bool
    income_preference: bool

    @field_validator("display_name")
    @classmethod
    def normalize_display_name(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("표시 이름을 입력해 주세요.")
        return normalized


class UserPreferencesResponse(UserPreferencesPayload):
    model_config = ConfigDict(from_attributes=True)

    updated_at: datetime
