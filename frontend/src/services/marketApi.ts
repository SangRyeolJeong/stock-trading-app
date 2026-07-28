import type {
  CandleSeries,
  ExchangeRate,
  InstrumentSearchResponse,
  OrderBook,
  Quote,
  SecurityOverview,
} from '../types/api';
import { apiClient } from './apiClient';

export type MarketFilter = 'all' | 'domestic' | 'overseas' | 'etf';

export const marketApi = {
  getQuote(symbol: string) {
    return apiClient<Quote>(`/api/v1/markets/quotes/${encodeURIComponent(symbol)}`);
  },
  getExchangeRate(baseCurrency: 'KRW' | 'USD', quoteCurrency: 'KRW' | 'USD') {
    return apiClient<ExchangeRate>(
      `/api/v1/markets/exchange-rates/${baseCurrency}/${quoteCurrency}`,
    );
  },
  searchInstruments(query = '', market: MarketFilter = 'all', limit = 50) {
    const params = new URLSearchParams({
      query,
      market,
      limit: String(limit),
    });
    return apiClient<InstrumentSearchResponse>(`/api/v1/markets/instruments?${params}`);
  },
  getCandles(symbol: string, limit = 120) {
    const params = new URLSearchParams({ interval: '1d', limit: String(limit) });
    return apiClient<CandleSeries>(
      `/api/v1/markets/candles/${encodeURIComponent(symbol)}?${params}`,
      { timeoutMs: 15_000 },
    );
  },
  getOrderBook(symbol: string) {
    return apiClient<OrderBook>(
      `/api/v1/markets/orderbooks/${encodeURIComponent(symbol)}`,
    );
  },
  getSecurityOverview(symbol: string) {
    return apiClient<SecurityOverview>(
      `/api/v1/markets/overview/${encodeURIComponent(symbol)}`,
    );
  },
};
