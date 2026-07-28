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

export interface Instrument {
  symbol: string;
  name: string;
  english_name: string | null;
  market: string;
  exchange_code: string;
  currency: 'KRW' | 'USD';
  asset_type: 'stock' | 'etf' | 'etn' | 'index' | 'other';
  country: 'KR' | 'US';
}

export interface InstrumentSearchResponse {
  items: Instrument[];
  total: number;
  source: 'builtin' | 'kis-master' | 'kis-master-cache';
  updated_at: string;
}

export interface Candle {
  date: string;
  open: string;
  high: string;
  low: string;
  close: string;
  volume: string;
}

export interface CandleSeries {
  symbol: string;
  currency: 'KRW' | 'USD';
  interval: '1d';
  source: 'mock' | 'kis';
  candles: Candle[];
  as_of: string;
}

export interface OrderBookLevel {
  price: string;
  quantity: string;
}

export interface OrderBook {
  symbol: string;
  currency: 'KRW' | 'USD';
  asks: OrderBookLevel[];
  bids: OrderBookLevel[];
  total_ask_quantity: string;
  total_bid_quantity: string;
  source: 'mock' | 'kis';
  delayed: boolean;
  as_of: string;
}

export interface SecurityOverview {
  symbol: string;
  name: string;
  market: string;
  asset_type: 'stock' | 'etf' | 'etn' | 'index' | 'other';
  currency: 'KRW' | 'USD';
  open: string | null;
  high: string | null;
  low: string | null;
  volume: string | null;
  week_52_high: string | null;
  week_52_low: string | null;
  per: string | null;
  pbr: string | null;
  eps: string | null;
  bps: string | null;
  source: 'mock' | 'kis';
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
  status: 'accepted' | 'filled' | 'rejected' | 'cancelled';
  symbol: string;
  name: string;
  currency: 'KRW' | 'USD';
  side: 'buy' | 'sell';
  order_type: 'market' | 'limit';
  quantity: string;
  limit_price: string | null;
  filled_price: string | null;
  gross_amount: string | null;
  fee: string | null;
  realized_pnl: string | null;
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
  liquidity_preference: boolean;
  fee_sensitivity: boolean;
  income_preference: boolean;
  tax_efficiency_priority: boolean;
}

export interface StrategyAllocation {
  asset_class: string;
  label: string;
  weight_pct: number;
  monthly_amount_krw: number;
  account_type: 'direct' | 'isa' | 'pension' | 'irp' | 'cash';
  product_example: string;
  role: string;
}

export interface StrategyReason {
  code: string;
  title: string;
  description: string;
}

export interface StrategyRiskSummary {
  level: StrategyRequest['risk_profile'];
  equity_weight_pct: number;
  defensive_weight_pct: number;
  liquidity_weight_pct: number;
  volatility_note: string;
}

export interface StrategyActionStep {
  order: number;
  title: string;
  description: string;
}

export interface StrategyResponse {
  engine_version: string;
  strategy_id: string;
  title: string;
  summary: string;
  score: number;
  allocation: Record<string, number>;
  allocations: StrategyAllocation[];
  reason_codes: string[];
  reasons: string[];
  rationale: StrategyReason[];
  risk_summary: StrategyRiskSummary;
  action_steps: StrategyActionStep[];
  warnings: string[];
  assumptions: string[];
  disclaimer: string;
}

export interface QuoteTick {
  symbol: string;
  price: number;
  as_of: string;
  source: string;
}

export type TaxAccountType = 'direct' | 'isa' | 'pension' | 'irp';

export interface TaxSimulationRequest {
  annual_salary_krw: number | string;
  monthly_contribution_krw: number | string;
  investment_years: number;
  annual_return_rate_pct: number | string;
  withdrawal_age: number;
}

export interface TaxRuleSource {
  title: string;
  url: string;
  authority: string;
}

export interface TaxAccountResult {
  account_type: TaxAccountType;
  name: string;
  tag: string;
  tax_description: string;
  contribution_limit_description: string;
  recommended_product: string;
  eligible_contribution: string;
  overflow_contribution: string;
  gross_value: string;
  contribution_tax_credit: string;
  investment_tax: string;
  withdrawal_tax: string;
  after_tax_value: string;
  tax_savings_vs_direct: string;
  score: number;
  benefits: string[];
  cautions: string[];
}

export interface TaxSimulationResponse {
  best_account_type: TaxAccountType;
  results: TaxAccountResult[];
  rules: {
    version: string;
    effective_date: string;
    parameters: Record<string, string>;
    sources: TaxRuleSource[];
  };
  assumptions: string[];
  disclaimer: string;
}
