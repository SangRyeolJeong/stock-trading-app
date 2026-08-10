import { beforeEach, describe, expect, it } from 'vitest';
import {
  buildGoalShareUrl,
  createGoalSnapshot,
  deleteGoalSnapshot,
  loadActiveGoalSnapshot,
  loadGoalStrategyMode,
  loadGoalSnapshots,
  parseGoalShareParams,
  saveGoalSnapshot,
  setActiveGoalSnapshot,
  setGoalStrategyMode,
  toggleGoalComparisonSelection,
  updateGoalSnapshotName,
  type GoalScenarioInputs,
} from './goalSnapshots';

const inputs: GoalScenarioInputs = {
  currentAssetsKrw: 10_000_000,
  targetAmountKrw: 300_000_000,
  monthlyContributionKrw: 500_000,
  investmentYears: 20,
  annualReturnRatePct: 7,
  annualInflationRatePct: 2,
  targetAmountInTodayMoney: true,
  annualContributionGrowthRatePct: 3,
};

const summary = {
  projectedValue: '284669799',
  achievementRatePct: '94.9',
  requiredMonthlyContribution: '531163',
  effectiveTargetAmount: '445784200',
  projectedValueInTodayMoney: '191579000',
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

  it('loads legacy share links with neutral inflation and contribution defaults', () => {
    expect(parseGoalShareParams(
      '#current=10000000&target=300000000&monthly=500000&years=20&return=7',
    )).toEqual({
      ...inputs,
      annualInflationRatePct: 0,
      targetAmountInTodayMoney: false,
      annualContributionGrowthRatePct: 0,
    });
  });

  it('stores, reloads and deletes a sanitized result snapshot', () => {
    const snapshot = createGoalSnapshot(
      inputs,
      summary,
      new Date('2026-08-03T00:00:00Z'),
    );

    expect(saveGoalSnapshot(snapshot)).toEqual([snapshot]);
    expect(loadGoalSnapshots()).toEqual([snapshot]);
    expect(deleteGoalSnapshot(snapshot.id)).toEqual([]);
    expect(loadGoalSnapshots()).toEqual([]);
  });

  it('keeps one active goal pointer in sync with rename and deletion', () => {
    const snapshot = createGoalSnapshot(
      inputs,
      summary,
      new Date('2026-08-03T00:00:00Z'),
      '내 집 마련',
    );
    saveGoalSnapshot(snapshot);

    expect(setActiveGoalSnapshot(snapshot.id)?.name).toBe('내 집 마련');
    expect(loadActiveGoalSnapshot()?.id).toBe(snapshot.id);
    expect(loadGoalStrategyMode()).toBe('active_goal');
    expect(setGoalStrategyMode('preferences')).toBe('preferences');
    expect(loadGoalStrategyMode()).toBe('preferences');
    updateGoalSnapshotName(snapshot.id, '수정한 목표');
    expect(loadActiveGoalSnapshot()?.name).toBe('수정한 목표');

    deleteGoalSnapshot(snapshot.id);
    expect(loadActiveGoalSnapshot()).toBeNull();
    expect(window.localStorage.getItem('moa-active-goal-snapshot-v1')).toBeNull();
    expect(loadGoalStrategyMode()).toBe('preferences');
  });

  it('rejects a missing active goal and cleans a stale pointer', () => {
    expect(() => setActiveGoalSnapshot('goal-missing')).toThrow('목표를 찾지 못했습니다');
    window.localStorage.setItem('moa-active-goal-snapshot-v1', 'goal-missing');
    window.localStorage.setItem('moa-goal-strategy-mode-v1', 'active_goal');

    expect(loadActiveGoalSnapshot()).toBeNull();
    expect(window.localStorage.getItem('moa-active-goal-snapshot-v1')).toBeNull();
    expect(window.localStorage.getItem('moa-goal-strategy-mode-v1')).toBeNull();
    expect(() => setGoalStrategyMode('active_goal')).toThrow('진행 목표가 없습니다');
  });

  it('adds a default name to legacy snapshots and persists a sanitized rename', () => {
    const snapshot = createGoalSnapshot(
      inputs,
      summary,
      new Date('2026-08-03T00:00:00Z'),
    );
    const legacySnapshot = {
      id: snapshot.id,
      savedAt: snapshot.savedAt,
      inputs: {
        currentAssetsKrw: snapshot.inputs.currentAssetsKrw,
        targetAmountKrw: snapshot.inputs.targetAmountKrw,
        monthlyContributionKrw: snapshot.inputs.monthlyContributionKrw,
        investmentYears: snapshot.inputs.investmentYears,
        annualReturnRatePct: snapshot.inputs.annualReturnRatePct,
      },
      summary: {
        projectedValue: snapshot.summary.projectedValue,
        achievementRatePct: snapshot.summary.achievementRatePct,
        requiredMonthlyContribution: snapshot.summary.requiredMonthlyContribution,
      },
    };
    window.localStorage.setItem('moa-goal-snapshots-v1', JSON.stringify([legacySnapshot]));

    expect(loadGoalSnapshots()[0]?.name).toBe('목표 300,000,000원 · 20년');
    expect(loadGoalSnapshots()[0]?.inputs).toEqual({
      ...inputs,
      annualInflationRatePct: 0,
      targetAmountInTodayMoney: false,
      annualContributionGrowthRatePct: 0,
    });
    expect(loadGoalSnapshots()[0]?.summary.effectiveTargetAmount).toBe('300000000');
    expect(loadGoalSnapshots()[0]?.summary.projectedValueInTodayMoney).toBe('284669799');
    expect(updateGoalSnapshotName(snapshot.id, '  내 집   마련 계획  ')[0]?.name).toBe(
      '내 집 마련 계획',
    );
    expect(loadGoalSnapshots()[0]?.name).toBe('내 집 마련 계획');
  });

  it('rejects an empty rename and keeps the saved order unchanged', () => {
    const first = createGoalSnapshot(
      inputs,
      summary,
      new Date('2026-08-03T00:00:00Z'),
      '첫 번째',
    );
    const second = createGoalSnapshot(inputs, {
      ...summary,
      projectedValue: '300000000',
      achievementRatePct: '100',
      requiredMonthlyContribution: '500000',
    }, new Date('2026-08-04T00:00:00Z'), '두 번째');
    saveGoalSnapshot(first);
    saveGoalSnapshot(second);

    expect(() => updateGoalSnapshotName(first.id, '   ')).toThrow('이름을 입력');
    expect(updateGoalSnapshotName(first.id, '변경된 첫 번째').map((item) => item.id)).toEqual([
      second.id,
      first.id,
    ]);
  });

  it('keeps only the ten most recent snapshots', () => {
    for (let index = 0; index < 12; index += 1) {
      saveGoalSnapshot(createGoalSnapshot(inputs, {
        ...summary,
        projectedValue: String(284_669_799 + index),
      }, new Date(`2026-08-03T00:00:${String(index).padStart(2, '0')}Z`)));
    }

    const snapshots = loadGoalSnapshots();
    expect(snapshots).toHaveLength(10);
    expect(snapshots[0].summary.projectedValue).toBe('284669810');
    expect(snapshots[snapshots.length - 1]?.summary.projectedValue).toBe('284669801');
  });

  it('selects at most two saved scenarios for comparison and allows deselection', () => {
    expect(toggleGoalComparisonSelection([], 'goal-a')).toEqual(['goal-a']);
    expect(toggleGoalComparisonSelection(['goal-a'], 'goal-b')).toEqual(['goal-a', 'goal-b']);
    expect(toggleGoalComparisonSelection(['goal-a', 'goal-b'], 'goal-c')).toEqual([
      'goal-a',
      'goal-b',
    ]);
    expect(toggleGoalComparisonSelection(['goal-a', 'goal-b'], 'goal-a')).toEqual(['goal-b']);
  });
});
