export interface Quote {
  symbol: string;
  name: string;
  currency: 'KRW' | 'USD';
  price: string;
  change: string;
  change_rate: string;
  market_open: boolean;
  delayed: boolean;
  as_of: string;
}

export interface PaperOrderRequest {
  symbol: string;
  side: 'buy' | 'sell';
  order_type: 'market' | 'limit';
  quantity: number;
  limit_price?: string;
  account_id: string;
  idempotency_key: string;
}

export interface PaperOrder {
  id: string;
  idempotency_key: string;
  status: 'accepted' | 'filled' | 'rejected';
  symbol: string;
  side: 'buy' | 'sell';
  quantity: number;
  filled_price: string;
  created_at: string;
}

export interface StrategyRequest {
  goal: 'retirement' | 'lump_sum' | 'cashflow';
  horizon_years: number;
  monthly_amount_krw: number;
  risk_profile: 'conservative' | 'balanced' | 'growth';
}

export interface StrategyResponse {
  title: string;
  score: number;
  allocation: Record<string, number>;
  reason_codes: string[];
  reasons: string[];
  disclaimer: string;
}

export interface QuoteTick {
  symbol: string;
  price: number;
  as_of: string;
  source: string;
}
