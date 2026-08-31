import type {
  StrategyExplanationResponse,
  StrategyRequest,
  StrategyResponse,
} from '../types/api';
import { apiClient } from './apiClient';

export const strategyApi = {
  recommend(request: StrategyRequest) {
    return apiClient<StrategyResponse>('/api/v1/strategies/recommend', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  },
  explain(request: StrategyRequest) {
    return apiClient<StrategyExplanationResponse>('/api/v1/strategies/explain', {
      method: 'POST',
      body: JSON.stringify(request),
      timeoutMs: 30_000,
    });
  },
};
