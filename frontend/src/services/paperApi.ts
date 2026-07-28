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
  getOrders(accountId = 'demo-account') {
    return apiClient<PaperOrder[]>(`/api/v1/paper/orders?account_id=${encodeURIComponent(accountId)}`);
  },
  getPositions(accountId = 'demo-account') {
    return apiClient<PaperPosition[]>(`/api/v1/paper/positions?account_id=${encodeURIComponent(accountId)}`);
  },
  getPortfolioSummary(accountId = 'demo-account') {
    return apiClient<PortfolioSummary>(
      `/api/v1/portfolios/summary?account_id=${encodeURIComponent(accountId)}`,
    );
  },
  createOrder(order: PaperOrderRequest) {
    return apiClient<PaperOrder>('/api/v1/paper/orders', {
      method: 'POST',
      body: JSON.stringify(order),
    });
  },
  cancelOrder(orderId: string, accountId = 'demo-account') {
    return apiClient<PaperOrder>(
      `/api/v1/paper/orders/${encodeURIComponent(orderId)}?account_id=${encodeURIComponent(accountId)}`,
      { method: 'DELETE' },
    );
  },
};
