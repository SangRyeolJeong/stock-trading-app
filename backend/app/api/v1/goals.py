from fastapi import APIRouter

from app.schemas.goal import GoalSimulationRequest, GoalSimulationResponse
from app.services.goal import goal_simulation_service

router = APIRouter(prefix="/goals", tags=["goals"])


@router.post("/simulate", response_model=GoalSimulationResponse)
async def simulate_goal(request: GoalSimulationRequest) -> GoalSimulationResponse:
    return goal_simulation_service.simulate(request)
