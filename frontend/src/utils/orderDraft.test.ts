import { describe, expect, it } from 'vitest';
import { calculateWholeShareOrderDraft } from './orderDraft';

describe('calculateWholeShareOrderDraft', () => {
  it('converts a KRW allocation to affordable whole USD shares including fees', () => {
    const draft = calculateWholeShareOrderDraft({
      allocationKrw: 1_000_000,
      priceUsd: 200,
      usdKrwRate: 1_400,
      feeRate: 0.001,
    });

    expect(draft.quantity).toBe(3);
    expect(draft.unitPriceKrw).toBe(280_000);
    expect(draft.grossAmountKrw).toBe(840_000);
    expect(draft.feeAmountKrw).toBe(840);
    expect(draft.totalAmountKrw).toBe(840_840);
    expect(draft.remainingKrw).toBe(159_160);
  });

  it('returns zero shares when the allocation cannot cover one share and its fee', () => {
    const draft = calculateWholeShareOrderDraft({
      allocationKrw: 300_000,
      priceUsd: 231.72,
      usdKrwRate: 1_385.2,
    });

    expect(draft.quantity).toBe(0);
    expect(draft.totalAmountKrw).toBe(0);
    expect(draft.remainingKrw).toBe(300_000);
  });

  it('handles unavailable price data without invalid numbers', () => {
    const draft = calculateWholeShareOrderDraft({
      allocationKrw: 500_000,
      priceUsd: 0,
      usdKrwRate: 1_400,
    });

    expect(draft.quantity).toBe(0);
    expect(draft.unitPriceKrw).toBe(0);
    expect(draft.remainingKrw).toBe(500_000);
  });
});
