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

export interface ExchangeRate {
  base_currency: 'KRW' | 'USD';
  quote_currency: 'KRW' | 'USD';
  rate: string;
  source: 'mock' | 'kis';
  delayed: boolean;
  as_of: string;
}

export interface PaperOrderRequest {
  symbol: string;
  side: 'buy' | 'sell';
  order_type: 'market' | 'limit';
  quantity: number | string;
  limit_price?: string;
  account_id: string;
  idempotency_key: string;
}

export interface PaperOrder {
  id: string;
  account_id: string;
  idempotency_key: string;
  status: 'accepted' | 'filled' | 'rejected';
  symbol: string;
  name: string;
  currency: 'KRW' | 'USD';
  side: 'buy' | 'sell';
  order_type: 'market' | 'limit';
  quantity: string;
  filled_price: string;
  gross_amount: string;
  fee: string;
  realized_pnl: string;
  created_at: string;
}

export interface CashBalance {
  currency: 'KRW' | 'USD';
  amount: string;
}

export interface PaperAccount {
  id: string;
  name: string;
  base_currency: 'KRW' | 'USD';
  cash_balances: CashBalance[];
  created_at: string;
}

export interface PaperPosition {
  id: string;
  account_id: string;
  symbol: string;
  name: string;
  currency: 'KRW' | 'USD';
  quantity: string;
  average_cost: string;
  realized_pnl: string;
  current_price: string | null;
  market_value: string | null;
  unrealized_pnl: string | null;
  return_rate: string | null;
  updated_at: string;
}

export interface PortfolioCurrencySummary {
  currency: 'KRW' | 'USD';
  cash: string;
  positions_value: string;
  total_value: string;
  unrealized_pnl: string;
  realized_pnl: string;
}

export interface PortfolioSummary {
  account_id: string;
  currencies: PortfolioCurrencySummary[];
  positions: PaperPosition[];
  as_of: string;
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
