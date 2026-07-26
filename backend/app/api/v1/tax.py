from fastapi import APIRouter

from app.schemas.tax import TaxSimulationRequest, TaxSimulationResponse
from app.services.tax import tax_calculation_service

router = APIRouter(prefix="/tax", tags=["tax"])


@router.post("/simulate", response_model=TaxSimulationResponse)
async def simulate_tax(request: TaxSimulationRequest) -> TaxSimulationResponse:
    return tax_calculation_service.simulate(request)
