import type { GoalSimulationRequest, GoalSimulationResponse } from '../types/api';
import { apiClient } from './apiClient';

export const goalApi = {
  simulate(request: GoalSimulationRequest) {
    return apiClient<GoalSimulationResponse>('/api/v1/goals/simulate', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  },
};
