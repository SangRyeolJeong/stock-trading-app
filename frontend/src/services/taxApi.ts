import type {
  PensionStartComparisonRequest,
  PensionStartComparisonResponse,
  TaxSimulationRequest,
  TaxSimulationResponse,
} from '../types/api';
import { apiClient } from './apiClient';

export const taxApi = {
  simulate(request: TaxSimulationRequest) {
    return apiClient<TaxSimulationResponse>('/api/v1/tax/simulate', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  },
  comparePensionStart(request: PensionStartComparisonRequest) {
    return apiClient<PensionStartComparisonResponse>('/api/v1/tax/pension-start', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  },
};
