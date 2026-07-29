import type {
  PaperAccount,
  PaperOrder,
  PaperOrderRequest,
  PaperPosition,
  PortfolioSummary,
} from '../types/api';
import { apiClient } from './apiClient';

export const paperApi = {
  getAccounts() {
    return apiClient<PaperAccount[]>('/api/v1/paper/accounts');
  },
  getOrders() {
    return apiClient<PaperOrder[]>('/api/v1/paper/orders');
  },
  getPositions() {
    return apiClient<PaperPosition[]>('/api/v1/paper/positions');
  },
  getPortfolioSummary() {
    return apiClient<PortfolioSummary>('/api/v1/portfolios/summary');
  },
  createOrder(order: PaperOrderRequest) {
    return apiClient<PaperOrder>('/api/v1/paper/orders', {
      method: 'POST',
      body: JSON.stringify(order),
    });
  },
  cancelOrder(orderId: string) {
    return apiClient<PaperOrder>(
      `/api/v1/paper/orders/${encodeURIComponent(orderId)}`,
      { method: 'DELETE' },
    );
  },
};
