export interface WatchlistItem {
  symbol: string;
  name: string;
  price: string;
  change: string;
  positive: boolean;
  color: string;
}

export interface Holding {
  symbol: string;
  name: string;
  quantity: string;
  value: string;
  profit: string;
  rate: string;
  positive: boolean;
  weight: number;
  color: string;
}

export const watchlist: WatchlistItem[] = [
  { symbol: 'QQQM', name: 'Invesco NASDAQ 100 ETF', price: '$231.72', change: '+1.28%', positive: true, color: '#3867ff' },
  { symbol: '005930', name: '삼성전자', price: '82,400원', change: '+0.61%', positive: true, color: '#2478ff' },
  { symbol: '360750', name: 'TIGER 미국S&P500', price: '22,165원', change: '-0.34%', positive: false, color: '#e95768' },
  { symbol: 'AAPL', name: 'Apple', price: '$219.31', change: '+0.92%', positive: true, color: '#202531' },
];

export const holdings: Holding[] = [
  { symbol: 'QQQM', name: 'Invesco NASDAQ 100 ETF', quantity: '38주', value: '12,438,120원', profit: '+1,184,300원', rate: '+10.52%', positive: true, weight: 42, color: '#5578ff' },
  { symbol: '360750', name: 'TIGER 미국S&P500', quantity: '214주', value: '4,743,310원', profit: '+318,540원', rate: '+7.20%', positive: true, weight: 26, color: '#6cd2b8' },
  { symbol: '005930', name: '삼성전자', quantity: '42주', value: '3,460,800원', profit: '-92,400원', rate: '-2.60%', positive: false, weight: 19, color: '#ffb15c' },
  { symbol: 'CASH', name: '예수금 · 달러', quantity: '$1,482', value: '2,044,520원', profit: '대기 자금', rate: '13.0%', positive: true, weight: 13, color: '#3d4758' },
];
