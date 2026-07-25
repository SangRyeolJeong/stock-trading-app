import type { StrategyRequest, StrategyResponse } from '../types/api';
import { apiClient } from './apiClient';

export const strategyApi = {
  recommend(request: StrategyRequest) {
    return apiClient<StrategyResponse>('/api/v1/strategies/recommend', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  },
};
