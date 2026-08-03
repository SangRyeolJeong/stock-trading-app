from fastapi import APIRouter

from app.schemas.tax import (
    PensionStartComparisonRequest,
    PensionStartComparisonResponse,
    TaxSimulationRequest,
    TaxSimulationResponse,
)
from app.services.tax import tax_calculation_service

router = APIRouter(prefix="/tax", tags=["tax"])


@router.post("/simulate", response_model=TaxSimulationResponse)
async def simulate_tax(request: TaxSimulationRequest) -> TaxSimulationResponse:
    return tax_calculation_service.simulate(request)


@router.post("/pension-start", response_model=PensionStartComparisonResponse)
async def compare_pension_start(
    request: PensionStartComparisonRequest,
) -> PensionStartComparisonResponse:
    return tax_calculation_service.compare_pension_start(request)
