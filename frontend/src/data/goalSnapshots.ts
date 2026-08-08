import { useSyncExternalStore } from 'react';

export interface GoalScenarioInputs {
  currentAssetsKrw: number;
  targetAmountKrw: number;
  monthlyContributionKrw: number;
  investmentYears: number;
  annualReturnRatePct: number;
  annualInflationRatePct: number;
  targetAmountInTodayMoney: boolean;
  annualContributionGrowthRatePct: number;
}

export interface GoalSnapshotSummary {
  projectedValue: string;
  achievementRatePct: string;
  requiredMonthlyContribution: string;
  effectiveTargetAmount: string;
  projectedValueInTodayMoney: string;
}

export interface GoalSnapshot {
  id: string;
  name: string;
  savedAt: string;
  inputs: GoalScenarioInputs;
  summary: GoalSnapshotSummary;
}

const STORAGE_KEY = 'moa-goal-snapshots-v1';
const ACTIVE_GOAL_STORAGE_KEY = 'moa-active-goal-snapshot-v1';
const MAX_SNAPSHOTS = 10;
export const MAX_GOAL_COMPARISON_SNAPSHOTS = 2;
const MAX_SNAPSHOT_NAME_LENGTH = 40;
const goalStoreListeners = new Set<() => void>();
let goalStoreRevision = 0;

function emitGoalStoreChange() {
  goalStoreRevision += 1;
  goalStoreListeners.forEach((listener) => listener());
}

function subscribeToGoalStore(listener: () => void) {
  goalStoreListeners.add(listener);
  return () => goalStoreListeners.delete(listener);
}

if (typeof window !== 'undefined') {
  window.addEventListener('storage', (event) => {
    if (![STORAGE_KEY, ACTIVE_GOAL_STORAGE_KEY].includes(event.key ?? '')) return;
    emitGoalStoreChange();
  });
}

function normalizeSnapshotName(value: unknown) {
  if (typeof value !== 'string') return '';
  return value.trim().replace(/\s+/g, ' ').slice(0, MAX_SNAPSHOT_NAME_LENGTH);
}

function defaultSnapshotName(inputs: GoalScenarioInputs) {
  return `목표 ${inputs.targetAmountKrw.toLocaleString('ko-KR')}원 · ${inputs.investmentYears}년`;
}

function isFiniteInRange(value: unknown, minimum: number, maximum: number) {
  const number = Number(value);
  return Number.isFinite(number) && number >= minimum && number <= maximum;
}

function sanitizeInputs(value: unknown): GoalScenarioInputs | null {
  if (!value || typeof value !== 'object') return null;
  const candidate = value as Partial<GoalScenarioInputs>;
  const annualInflationRatePct = candidate.annualInflationRatePct ?? 0;
  const targetAmountInTodayMoney = candidate.targetAmountInTodayMoney ?? false;
  const annualContributionGrowthRatePct = candidate.annualContributionGrowthRatePct ?? 0;
  if (
    !isFiniteInRange(candidate.currentAssetsKrw, 0, 1_000_000_000_000)
    || !isFiniteInRange(candidate.targetAmountKrw, 1, 10_000_000_000_000)
    || !isFiniteInRange(candidate.monthlyContributionKrw, 0, 100_000_000)
    || !isFiniteInRange(candidate.investmentYears, 1, 50)
    || !Number.isInteger(Number(candidate.investmentYears))
    || !isFiniteInRange(candidate.annualReturnRatePct, -100, 30)
    || !isFiniteInRange(annualInflationRatePct, 0, 20)
    || typeof targetAmountInTodayMoney !== 'boolean'
    || !isFiniteInRange(annualContributionGrowthRatePct, 0, 20)
  ) return null;
  return {
    currentAssetsKrw: Number(candidate.currentAssetsKrw),
    targetAmountKrw: Number(candidate.targetAmountKrw),
    monthlyContributionKrw: Number(candidate.monthlyContributionKrw),
    investmentYears: Number(candidate.investmentYears),
    annualReturnRatePct: Number(candidate.annualReturnRatePct),
    annualInflationRatePct: Number(annualInflationRatePct),
    targetAmountInTodayMoney,
    annualContributionGrowthRatePct: Number(annualContributionGrowthRatePct),
  };
}

function sanitizeSummary(
  value: unknown,
  inputs: GoalScenarioInputs,
): GoalSnapshotSummary | null {
  if (!value || typeof value !== 'object') return null;
  const candidate = value as Partial<GoalSnapshotSummary>;
  const values = [
    candidate.projectedValue,
    candidate.achievementRatePct,
    candidate.requiredMonthlyContribution,
    candidate.effectiveTargetAmount ?? inputs.targetAmountKrw,
    candidate.projectedValueInTodayMoney ?? candidate.projectedValue,
  ];
  if (values.some((item) => !Number.isFinite(Number(item)) || Number(item) < 0)) {
    return null;
  }
  return {
    projectedValue: String(candidate.projectedValue),
    achievementRatePct: String(candidate.achievementRatePct),
    requiredMonthlyContribution: String(candidate.requiredMonthlyContribution),
    effectiveTargetAmount: String(
      candidate.effectiveTargetAmount ?? inputs.targetAmountKrw,
    ),
    projectedValueInTodayMoney: String(
      candidate.projectedValueInTodayMoney ?? candidate.projectedValue,
    ),
  };
}

function sanitizeSnapshot(value: unknown): GoalSnapshot | null {
  if (!value || typeof value !== 'object') return null;
  const candidate = value as Partial<GoalSnapshot>;
  const inputs = sanitizeInputs(candidate.inputs);
  const summary = inputs ? sanitizeSummary(candidate.summary, inputs) : null;
  if (
    typeof candidate.id !== 'string'
    || !candidate.id
    || typeof candidate.savedAt !== 'string'
    || Number.isNaN(Date.parse(candidate.savedAt))
    || !inputs
    || !summary
  ) return null;
  return {
    id: candidate.id,
    name: normalizeSnapshotName(candidate.name) || defaultSnapshotName(inputs),
    savedAt: candidate.savedAt,
    inputs,
    summary,
  };
}

export function parseGoalShareParams(fragment: string): GoalScenarioInputs | null {
  const params = new URLSearchParams(fragment.replace(/^#/, ''));
  if (!['current', 'target', 'monthly', 'years', 'return'].every((key) => params.has(key))) {
    return null;
  }
  if (params.has('today') && !['0', '1'].includes(params.get('today') ?? '')) return null;
  return sanitizeInputs({
    currentAssetsKrw: params.get('current'),
    targetAmountKrw: params.get('target'),
    monthlyContributionKrw: params.get('monthly'),
    investmentYears: params.get('years'),
    annualReturnRatePct: params.get('return'),
    annualInflationRatePct: params.get('inflation') ?? 0,
    targetAmountInTodayMoney: params.get('today') === '1',
    annualContributionGrowthRatePct: params.get('growth') ?? 0,
  });
}

export function buildGoalShareUrl(
  inputs: GoalScenarioInputs,
  baseUrl = window.location.origin,
) {
  const sanitized = sanitizeInputs(inputs);
  if (!sanitized) throw new Error('공유할 목표 계산 조건이 올바르지 않습니다.');
  const url = new URL('/goal-simulator', baseUrl);
  const params = new URLSearchParams();
  params.set('current', String(sanitized.currentAssetsKrw));
  params.set('target', String(sanitized.targetAmountKrw));
  params.set('monthly', String(sanitized.monthlyContributionKrw));
  params.set('years', String(sanitized.investmentYears));
  params.set('return', String(sanitized.annualReturnRatePct));
  params.set('inflation', String(sanitized.annualInflationRatePct));
  params.set('today', sanitized.targetAmountInTodayMoney ? '1' : '0');
  params.set('growth', String(sanitized.annualContributionGrowthRatePct));
  url.hash = params.toString();
  return url.toString();
}

export function createGoalSnapshot(
  inputs: GoalScenarioInputs,
  summary: GoalSnapshotSummary,
  now = new Date(),
  name = '',
): GoalSnapshot {
  const sanitizedInputs = sanitizeInputs(inputs);
  const sanitizedSummary = sanitizedInputs
    ? sanitizeSummary(summary, sanitizedInputs)
    : null;
  if (!sanitizedInputs || !sanitizedSummary) {
    throw new Error('저장할 목표 계산 결과가 올바르지 않습니다.');
  }
  const randomId = globalThis.crypto?.randomUUID?.()
    ?? `${now.getTime()}-${Math.random().toString(36).slice(2)}`;
  return {
    id: `goal-${randomId}`,
    name: normalizeSnapshotName(name) || defaultSnapshotName(sanitizedInputs),
    savedAt: now.toISOString(),
    inputs: sanitizedInputs,
    summary: sanitizedSummary,
  };
}

export function loadGoalSnapshots(): GoalSnapshot[] {
  try {
    const parsed = JSON.parse(window.localStorage.getItem(STORAGE_KEY) ?? '[]') as unknown;
    if (!Array.isArray(parsed)) return [];
    return parsed
      .map(sanitizeSnapshot)
      .filter((item): item is GoalSnapshot => item !== null)
      .slice(0, MAX_SNAPSHOTS);
  } catch {
    return [];
  }
}

export function saveGoalSnapshot(snapshot: GoalSnapshot): GoalSnapshot[] {
  const sanitized = sanitizeSnapshot(snapshot);
  if (!sanitized) throw new Error('저장할 목표 계산 결과가 올바르지 않습니다.');
  const next = [
    sanitized,
    ...loadGoalSnapshots().filter((item) => item.id !== sanitized.id),
  ].slice(0, MAX_SNAPSHOTS);
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
  const activeGoalId = window.localStorage.getItem(ACTIVE_GOAL_STORAGE_KEY);
  if (activeGoalId && !next.some((item) => item.id === activeGoalId)) {
    window.localStorage.removeItem(ACTIVE_GOAL_STORAGE_KEY);
  }
  emitGoalStoreChange();
  return next;
}

export function deleteGoalSnapshot(snapshotId: string): GoalSnapshot[] {
  const next = loadGoalSnapshots().filter((item) => item.id !== snapshotId);
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
  if (window.localStorage.getItem(ACTIVE_GOAL_STORAGE_KEY) === snapshotId) {
    window.localStorage.removeItem(ACTIVE_GOAL_STORAGE_KEY);
  }
  emitGoalStoreChange();
  return next;
}

export function updateGoalSnapshotName(snapshotId: string, name: string): GoalSnapshot[] {
  const sanitizedName = normalizeSnapshotName(name);
  if (!sanitizedName) throw new Error('시나리오 이름을 입력해주세요.');
  const snapshots = loadGoalSnapshots();
  if (!snapshots.some((snapshot) => snapshot.id === snapshotId)) {
    throw new Error('이름을 변경할 시나리오를 찾지 못했습니다.');
  }
  const next = snapshots.map((snapshot) => (
    snapshot.id === snapshotId ? { ...snapshot, name: sanitizedName } : snapshot
  ));
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
  emitGoalStoreChange();
  return next;
}

export function loadActiveGoalSnapshot(): GoalSnapshot | null {
  const activeGoalId = window.localStorage.getItem(ACTIVE_GOAL_STORAGE_KEY);
  if (!activeGoalId) return null;
  const snapshot = loadGoalSnapshots().find((item) => item.id === activeGoalId) ?? null;
  if (!snapshot) window.localStorage.removeItem(ACTIVE_GOAL_STORAGE_KEY);
  return snapshot;
}

export function setActiveGoalSnapshot(snapshotId: string | null): GoalSnapshot | null {
  if (snapshotId === null) {
    window.localStorage.removeItem(ACTIVE_GOAL_STORAGE_KEY);
    emitGoalStoreChange();
    return null;
  }
  const snapshot = loadGoalSnapshots().find((item) => item.id === snapshotId);
  if (!snapshot) throw new Error('진행 중으로 설정할 목표를 찾지 못했습니다.');
  window.localStorage.setItem(ACTIVE_GOAL_STORAGE_KEY, snapshot.id);
  emitGoalStoreChange();
  return snapshot;
}

export function useActiveGoalSnapshot(): GoalSnapshot | null {
  useSyncExternalStore(
    subscribeToGoalStore,
    () => goalStoreRevision,
    () => 0,
  );
  return loadActiveGoalSnapshot();
}

export function toggleGoalComparisonSelection(
  selectedIds: string[],
  snapshotId: string,
): string[] {
  if (selectedIds.includes(snapshotId)) {
    return selectedIds.filter((id) => id !== snapshotId);
  }
  if (selectedIds.length >= MAX_GOAL_COMPARISON_SNAPSHOTS) return selectedIds;
  return [...selectedIds, snapshotId];
}
