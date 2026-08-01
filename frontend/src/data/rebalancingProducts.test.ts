import { describe, expect, it } from 'vitest';
import { categoryForPosition, REBALANCING_PRODUCTS } from './rebalancingProducts';

describe('rebalancing product metadata', () => {
  it('maps the example ETFs to distinct strategy categories and official sources', () => {
    expect(REBALANCING_PRODUCTS.map((product) => product.category)).toEqual([
      'growth',
      'income',
      'defensive',
    ]);
    expect(REBALANCING_PRODUCTS.every(
      (product) => product.officialSourceUrl.startsWith('https://'),
    )).toBe(true);
  });

  it('classifies supported income and defensive positions and defaults others to growth', () => {
    expect(categoryForPosition('dgro')).toBe('income');
    expect(categoryForPosition('SGOV')).toBe('defensive');
    expect(categoryForPosition('QQQM')).toBe('growth');
    expect(categoryForPosition('AAPL')).toBe('growth');
  });
});
