import type { PaperOrder, PaperOrderRequest } from '../types/api';
import { apiClient } from './apiClient';

export const paperApi = {
  createOrder(order: PaperOrderRequest) {
    return apiClient<PaperOrder>('/api/v1/paper/orders', {
      method: 'POST',
      body: JSON.stringify(order),
    });
  },
};
