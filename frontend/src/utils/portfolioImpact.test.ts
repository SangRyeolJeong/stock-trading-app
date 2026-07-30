import { describe, expect, it } from 'vitest';
import { calculateOrderImpact } from './portfolioImpact';

describe('calculateOrderImpact', () => {
  it('converts mixed-currency holdings and projects a buy', () => {
    const impact = calculateOrderImpact({
      symbol: 'QQQM',
      side: 'buy',
      tradeCurrency: 'USD',
      grossAmount: 500,
      feeAmount: 0.5,
      availableCash: 2_000,
      usdKrwRate: 1_400,
      positions: [
        { symbol: 'QQQM', currency: 'USD', marketValue: 1_000 },
        { symbol: '005930', currency: 'KRW', marketValue: 1_400_000 },
      ],
    });

    expect(impact.currentInvestedKrw).toBe(2_800_000);
    expect(impact.projectedInvestedKrw).toBe(3_500_000);
    expect(impact.currentWeightPct).toBe(50);
    expect(impact.projectedWeightPct).toBe(60);
    expect(impact.projectedCash).toBe(1_499.5);
    expect(impact.concentrationLevel).toBe('high');
  });

  it('projects a sale without allowing negative position values', () => {
    const impact = calculateOrderImpact({
      symbol: 'AAPL',
      side: 'sell',
      tradeCurrency: 'USD',
      grossAmount: 250,
      feeAmount: 0.25,
      availableCash: 500,
      usdKrwRate: 1_400,
      positions: [
        { symbol: 'AAPL', currency: 'USD', marketValue: 250 },
        { symbol: 'QQQM', currency: 'USD', marketValue: 750 },
      ],
    });

    expect(impact.projectedSymbolValueKrw).toBe(0);
    expect(impact.projectedWeightPct).toBe(0);
    expect(impact.projectedCash).toBe(749.75);
    expect(impact.concentrationLevel).toBe('balanced');
  });

  it('treats the first purchase as a fully concentrated position', () => {
    const impact = calculateOrderImpact({
      symbol: 'VOO',
      side: 'buy',
      tradeCurrency: 'USD',
      grossAmount: 100,
      feeAmount: 0.1,
      availableCash: 1_000,
      usdKrwRate: 1_400,
      positions: [],
    });

    expect(impact.currentWeightPct).toBe(0);
    expect(impact.projectedWeightPct).toBe(100);
    expect(impact.concentrationLevel).toBe('high');
  });
});
