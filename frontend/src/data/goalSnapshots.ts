export interface GoalScenarioInputs {
  currentAssetsKrw: number;
  targetAmountKrw: number;
  monthlyContributionKrw: number;
  investmentYears: number;
  annualReturnRatePct: number;
}

export interface GoalSnapshotSummary {
  projectedValue: string;
  achievementRatePct: string;
  requiredMonthlyContribution: string;
}

export interface GoalSnapshot {
  id: string;
  savedAt: string;
  inputs: GoalScenarioInputs;
  summary: GoalSnapshotSummary;
}

const STORAGE_KEY = 'moa-goal-snapshots-v1';
const MAX_SNAPSHOTS = 10;

function isFiniteInRange(value: unknown, minimum: number, maximum: number) {
  const number = Number(value);
  return Number.isFinite(number) && number >= minimum && number <= maximum;
}

function sanitizeInputs(value: unknown): GoalScenarioInputs | null {
  if (!value || typeof value !== 'object') return null;
  const candidate = value as Partial<GoalScenarioInputs>;
  if (
    !isFiniteInRange(candidate.currentAssetsKrw, 0, 1_000_000_000_000)
    || !isFiniteInRange(candidate.targetAmountKrw, 1, 10_000_000_000_000)
    || !isFiniteInRange(candidate.monthlyContributionKrw, 0, 100_000_000)
    || !isFiniteInRange(candidate.investmentYears, 1, 50)
    || !Number.isInteger(Number(candidate.investmentYears))
    || !isFiniteInRange(candidate.annualReturnRatePct, -100, 30)
  ) return null;
  return {
    currentAssetsKrw: Number(candidate.currentAssetsKrw),
    targetAmountKrw: Number(candidate.targetAmountKrw),
    monthlyContributionKrw: Number(candidate.monthlyContributionKrw),
    investmentYears: Number(candidate.investmentYears),
    annualReturnRatePct: Number(candidate.annualReturnRatePct),
  };
}

function sanitizeSummary(value: unknown): GoalSnapshotSummary | null {
  if (!value || typeof value !== 'object') return null;
  const candidate = value as Partial<GoalSnapshotSummary>;
  const values = [
    candidate.projectedValue,
    candidate.achievementRatePct,
    candidate.requiredMonthlyContribution,
  ];
  if (values.some((item) => !Number.isFinite(Number(item)) || Number(item) < 0)) {
    return null;
  }
  return {
    projectedValue: String(candidate.projectedValue),
    achievementRatePct: String(candidate.achievementRatePct),
    requiredMonthlyContribution: String(candidate.requiredMonthlyContribution),
  };
}

function sanitizeSnapshot(value: unknown): GoalSnapshot | null {
  if (!value || typeof value !== 'object') return null;
  const candidate = value as Partial<GoalSnapshot>;
  const inputs = sanitizeInputs(candidate.inputs);
  const summary = sanitizeSummary(candidate.summary);
  if (
    typeof candidate.id !== 'string'
    || !candidate.id
    || typeof candidate.savedAt !== 'string'
    || Number.isNaN(Date.parse(candidate.savedAt))
    || !inputs
    || !summary
  ) return null;
  return { id: candidate.id, savedAt: candidate.savedAt, inputs, summary };
}

export function parseGoalShareParams(fragment: string): GoalScenarioInputs | null {
  const params = new URLSearchParams(fragment.replace(/^#/, ''));
  if (!['current', 'target', 'monthly', 'years', 'return'].every((key) => params.has(key))) {
    return null;
  }
  return sanitizeInputs({
    currentAssetsKrw: params.get('current'),
    targetAmountKrw: params.get('target'),
    monthlyContributionKrw: params.get('monthly'),
    investmentYears: params.get('years'),
    annualReturnRatePct: params.get('return'),
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
  url.hash = params.toString();
  return url.toString();
}

export function createGoalSnapshot(
  inputs: GoalScenarioInputs,
  summary: GoalSnapshotSummary,
  now = new Date(),
): GoalSnapshot {
  const sanitizedInputs = sanitizeInputs(inputs);
  const sanitizedSummary = sanitizeSummary(summary);
  if (!sanitizedInputs || !sanitizedSummary) {
    throw new Error('저장할 목표 계산 결과가 올바르지 않습니다.');
  }
  const randomId = globalThis.crypto?.randomUUID?.()
    ?? `${now.getTime()}-${Math.random().toString(36).slice(2)}`;
  return {
    id: `goal-${randomId}`,
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
  return next;
}

export function deleteGoalSnapshot(snapshotId: string): GoalSnapshot[] {
  const next = loadGoalSnapshots().filter((item) => item.id !== snapshotId);
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
  return next;
}
