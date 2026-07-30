export type ImpactCurrency = 'KRW' | 'USD';
export type ImpactSide = 'buy' | 'sell';

export interface ImpactPosition {
  symbol: string;
  currency: ImpactCurrency;
  marketValue: number;
}

export interface OrderImpactInput {
  symbol: string;
  side: ImpactSide;
  tradeCurrency: ImpactCurrency;
  grossAmount: number;
  feeAmount: number;
  availableCash: number;
  usdKrwRate: number;
  positions: ImpactPosition[];
}

export interface OrderImpact {
  currentWeightPct: number;
  projectedWeightPct: number;
  currentInvestedKrw: number;
  projectedInvestedKrw: number;
  projectedSymbolValueKrw: number;
  projectedCash: number;
  concentrationLevel: 'balanced' | 'watch' | 'high';
}

function toKrw(value: number, currency: ImpactCurrency, usdKrwRate: number) {
  return currency === 'USD' ? value * usdKrwRate : value;
}

export function calculateOrderImpact(input: OrderImpactInput): OrderImpact {
  const currentInvestedKrw = input.positions.reduce(
    (total, position) => total + toKrw(
      Math.max(0, position.marketValue),
      position.currency,
      input.usdKrwRate,
    ),
    0,
  );
  const currentSymbolValueKrw = input.positions
    .filter((position) => position.symbol === input.symbol)
    .reduce(
      (total, position) => total + toKrw(
        Math.max(0, position.marketValue),
        position.currency,
        input.usdKrwRate,
      ),
      0,
    );
  const signedGrossKrw = toKrw(
    Math.max(0, input.grossAmount),
    input.tradeCurrency,
    input.usdKrwRate,
  ) * (input.side === 'buy' ? 1 : -1);
  const projectedInvestedKrw = Math.max(0, currentInvestedKrw + signedGrossKrw);
  const projectedSymbolValueKrw = Math.max(0, currentSymbolValueKrw + signedGrossKrw);
  const currentWeightPct = currentInvestedKrw > 0
    ? currentSymbolValueKrw / currentInvestedKrw * 100
    : 0;
  const projectedWeightPct = projectedInvestedKrw > 0
    ? projectedSymbolValueKrw / projectedInvestedKrw * 100
    : 0;
  const cashDelta = input.side === 'buy'
    ? -(input.grossAmount + input.feeAmount)
    : input.grossAmount - input.feeAmount;
  const projectedCash = Math.max(0, input.availableCash + cashDelta);
  const concentrationLevel = projectedWeightPct >= 40
    ? 'high'
    : projectedWeightPct >= 25
      ? 'watch'
      : 'balanced';

  return {
    currentWeightPct,
    projectedWeightPct,
    currentInvestedKrw,
    projectedInvestedKrw,
    projectedSymbolValueKrw,
    projectedCash,
    concentrationLevel,
  };
}
