export type RebalancingCategory = 'equity' | 'defensive' | 'cash';

export interface RebalancingInput {
  currentValuesKrw: Record<RebalancingCategory, number>;
  targetWeightsPct: Record<RebalancingCategory, number>;
  contributionKrw: number;
}

export interface RebalancingItem {
  category: RebalancingCategory;
  currentValueKrw: number;
  currentWeightPct: number;
  targetWeightPct: number;
  driftPctPoint: number;
  suggestedContributionKrw: number;
}

export interface RebalancingPlan {
  currentTotalKrw: number;
  projectedTotalKrw: number;
  contributionKrw: number;
  items: RebalancingItem[];
}

const CATEGORIES: RebalancingCategory[] = ['equity', 'defensive', 'cash'];

export function calculateRebalancingPlan(input: RebalancingInput): RebalancingPlan {
  const currentValues = Object.fromEntries(
    CATEGORIES.map((category) => [
      category,
      Math.max(0, input.currentValuesKrw[category] ?? 0),
    ]),
  ) as Record<RebalancingCategory, number>;
  const contributionKrw = Math.max(0, Math.round(input.contributionKrw));
  const currentTotalKrw = CATEGORIES.reduce(
    (total, category) => total + currentValues[category],
    0,
  );
  const projectedTotalKrw = currentTotalKrw + contributionKrw;
  const gaps = Object.fromEntries(
    CATEGORIES.map((category) => [
      category,
      Math.max(
        0,
        projectedTotalKrw * input.targetWeightsPct[category] / 100
          - currentValues[category],
      ),
    ]),
  ) as Record<RebalancingCategory, number>;
  const totalGap = CATEGORIES.reduce((total, category) => total + gaps[category], 0);
  let allocated = 0;

  const items = CATEGORIES.map((category, index): RebalancingItem => {
    const isLast = index === CATEGORIES.length - 1;
    const proportionalAmount = totalGap > 0
      ? Math.round(contributionKrw * gaps[category] / totalGap)
      : Math.round(contributionKrw * input.targetWeightsPct[category] / 100);
    const suggestedContributionKrw = isLast
      ? contributionKrw - allocated
      : Math.min(contributionKrw - allocated, proportionalAmount);
    allocated += suggestedContributionKrw;
    const currentWeightPct = currentTotalKrw > 0
      ? currentValues[category] / currentTotalKrw * 100
      : 0;

    return {
      category,
      currentValueKrw: currentValues[category],
      currentWeightPct,
      targetWeightPct: input.targetWeightsPct[category],
      driftPctPoint: currentWeightPct - input.targetWeightsPct[category],
      suggestedContributionKrw,
    };
  });

  return {
    currentTotalKrw,
    projectedTotalKrw,
    contributionKrw,
    items,
  };
}
