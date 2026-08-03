from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field

GoalScenarioKind = Literal["lower", "base", "higher"]


class GoalSimulationRequest(BaseModel):
    current_assets_krw: Decimal = Field(ge=0, le=Decimal("1000000000000"))
    target_amount_krw: Decimal = Field(gt=0, le=Decimal("10000000000000"))
    monthly_contribution_krw: Decimal = Field(ge=0, le=Decimal("100000000"))
    investment_years: int = Field(ge=1, le=50)
    annual_return_rate_pct: Decimal = Field(ge=Decimal("-100"), le=Decimal("30"))


class GoalMilestone(BaseModel):
    year: int
    contributed_principal: Decimal
    projected_value: Decimal
    target_achievement_rate_pct: Decimal


class GoalSensitivityScenario(BaseModel):
    kind: GoalScenarioKind
    annual_return_rate_pct: Decimal
    projected_value: Decimal
    target_achievement_rate_pct: Decimal


class GoalSimulationResponse(BaseModel):
    engine_version: str
    projected_value: Decimal
    total_contributed_principal: Decimal
    investment_gain: Decimal
    target_gap: Decimal
    target_surplus: Decimal
    target_achievement_rate_pct: Decimal
    required_monthly_contribution: Decimal
    additional_monthly_contribution: Decimal
    required_monthly_within_supported_limit: bool
    milestones: list[GoalMilestone]
    sensitivity: list[GoalSensitivityScenario]
    assumptions: list[str]
    formula: str
    disclaimer: str
