import type { RebalancingCategory } from '../utils/rebalancing';

export type InvestableRebalancingCategory = Exclude<RebalancingCategory, 'cash'>;

export interface RebalancingProduct {
  category: InvestableRebalancingCategory;
  symbol: string;
  name: string;
  role: string;
  logo: string;
  officialSourceUrl: string;
}

export const REBALANCING_PRODUCTS: RebalancingProduct[] = [
  {
    category: 'growth',
    symbol: 'QQQM',
    name: 'Invesco NASDAQ 100 ETF',
    role: '성장주식 예시',
    logo: 'Q',
    officialSourceUrl: 'https://www.invesco.com/us/en/solutions/innovation-suite.html',
  },
  {
    category: 'income',
    symbol: 'DGRO',
    name: 'iShares Core Dividend Growth ETF',
    role: '배당·인컴 예시',
    logo: 'D',
    officialSourceUrl: 'https://www.ishares.com/us/products/264623/ishares-core-dividend-growth-etf',
  },
  {
    category: 'defensive',
    symbol: 'SGOV',
    name: 'iShares 0-3 Month Treasury Bond ETF',
    role: '초단기 국채·방어 예시',
    logo: 'S',
    officialSourceUrl: 'https://www.ishares.com/us/products/314116/ishares-0-3-month-treasury-bond-etf',
  },
];

const CATEGORY_BY_SYMBOL = Object.fromEntries(
  REBALANCING_PRODUCTS.map((product) => [product.symbol, product.category]),
) as Partial<Record<string, InvestableRebalancingCategory>>;

export function categoryForPosition(symbol: string): InvestableRebalancingCategory {
  return CATEGORY_BY_SYMBOL[symbol.trim().toUpperCase()] ?? 'growth';
}
