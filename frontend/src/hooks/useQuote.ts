import { useQuery } from '@tanstack/react-query';
import { marketApi } from '../services/marketApi';

export function useQuote(symbol: string) {
  return useQuery({
    queryKey: ['quote', symbol],
    queryFn: () => marketApi.getQuote(symbol),
    enabled: Boolean(symbol),
  });
}
