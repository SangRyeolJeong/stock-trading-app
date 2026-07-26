import type { ExchangeRate, Quote } from '../types/api';
import { apiClient } from './apiClient';

export const marketApi = {
  getQuote(symbol: string) {
    return apiClient<Quote>(`/api/v1/markets/quotes/${encodeURIComponent(symbol)}`);
  },
  getExchangeRate(baseCurrency: 'KRW' | 'USD', quoteCurrency: 'KRW' | 'USD') {
    return apiClient<ExchangeRate>(
      `/api/v1/markets/exchange-rates/${baseCurrency}/${quoteCurrency}`,
    );
  },
};
