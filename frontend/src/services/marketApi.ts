import type { Quote } from '../types/api';
import { apiClient } from './apiClient';

export const marketApi = {
  getQuote(symbol: string) {
    return apiClient<Quote>(`/api/v1/markets/quotes/${encodeURIComponent(symbol)}`);
  },
};
