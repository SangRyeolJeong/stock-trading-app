from typing import Literal

from pydantic import BaseModel, Field

StrategyGoal = Literal["retirement", "lump_sum", "cashflow"]
RiskProfile = Literal["conservative", "balanced", "growth"]
AccountType = Literal["direct", "isa", "pension", "irp", "cash"]


class StrategyRequest(BaseModel):
    goal: StrategyGoal = "retirement"
    horizon_years: int = Field(default=30, ge=1, le=50)
    monthly_amount_krw: int = Field(default=500_000, ge=10_000, le=100_000_000)
    risk_profile: RiskProfile = "growth"
    liquidity_preference: bool = True
    fee_sensitivity: bool = True
    income_preference: bool = False
    tax_efficiency_priority: bool = True


class StrategyAllocation(BaseModel):
    asset_class: str
    label: str
    weight_pct: int
    monthly_amount_krw: int
    account_type: AccountType
    product_example: str
    role: str


class StrategyReason(BaseModel):
    code: str
    title: str
    description: str


class StrategyRiskSummary(BaseModel):
    level: RiskProfile
    equity_weight_pct: int
    defensive_weight_pct: int
    liquidity_weight_pct: int
    volatility_note: str


class StrategyActionStep(BaseModel):
    order: int
    title: str
    description: str


class StrategyResponse(BaseModel):
    engine_version: str
    strategy_id: str
    title: str
    summary: str
    score: int
    allocation: dict[str, int]
    allocations: list[StrategyAllocation]
    reason_codes: list[str]
    reasons: list[str]
    rationale: list[StrategyReason]
    risk_summary: StrategyRiskSummary
    action_steps: list[StrategyActionStep]
    warnings: list[str]
    assumptions: list[str]
    disclaimer: str
