import { beforeEach, describe, expect, it } from 'vitest';
import {
  buildGoalShareUrl,
  createGoalSnapshot,
  deleteGoalSnapshot,
  loadGoalSnapshots,
  parseGoalShareParams,
  saveGoalSnapshot,
  type GoalScenarioInputs,
} from './goalSnapshots';

const inputs: GoalScenarioInputs = {
  currentAssetsKrw: 10_000_000,
  targetAmountKrw: 300_000_000,
  monthlyContributionKrw: 500_000,
  investmentYears: 20,
  annualReturnRatePct: 7,
};

describe('goalSnapshots', () => {
  beforeEach(() => {
    window.localStorage.clear();
  });

  it('round-trips every calculation input through a share URL', () => {
    const url = buildGoalShareUrl(inputs, 'https://moa.example');

    expect(parseGoalShareParams(new URL(url).hash)).toEqual(inputs);
    expect(url).toContain('/goal-simulator#');
    expect(new URL(url).search).toBe('');
  });

  it('rejects incomplete or unsafe shared inputs', () => {
    expect(parseGoalShareParams('?target=300000000')).toBeNull();
    expect(parseGoalShareParams(
      '?current=0&target=300000000&monthly=-1&years=20&return=7',
    )).toBeNull();
  });

  it('stores, reloads and deletes a sanitized result snapshot', () => {
    const snapshot = createGoalSnapshot(inputs, {
      projectedValue: '284669799',
      achievementRatePct: '94.9',
      requiredMonthlyContribution: '531163',
    }, new Date('2026-08-03T00:00:00Z'));

    expect(saveGoalSnapshot(snapshot)).toEqual([snapshot]);
    expect(loadGoalSnapshots()).toEqual([snapshot]);
    expect(deleteGoalSnapshot(snapshot.id)).toEqual([]);
    expect(loadGoalSnapshots()).toEqual([]);
  });

  it('keeps only the ten most recent snapshots', () => {
    for (let index = 0; index < 12; index += 1) {
      saveGoalSnapshot(createGoalSnapshot(inputs, {
        projectedValue: String(284_669_799 + index),
        achievementRatePct: '94.9',
        requiredMonthlyContribution: '531163',
      }, new Date(`2026-08-03T00:00:${String(index).padStart(2, '0')}Z`)));
    }

    const snapshots = loadGoalSnapshots();
    expect(snapshots).toHaveLength(10);
    expect(snapshots[0].summary.projectedValue).toBe('284669810');
    expect(snapshots[snapshots.length - 1]?.summary.projectedValue).toBe('284669801');
  });
});
