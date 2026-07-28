import { useSyncExternalStore } from 'react';

export type StrategyGoal = 'retirement' | 'lump_sum' | 'cashflow';
export type RiskProfile = 'conservative' | 'balanced' | 'growth';

export interface UserPreferences {
  displayName: string;
  annualSalaryKrw: number;
  monthlyInvestmentKrw: number;
  investmentYears: number;
  annualReturnRatePct: number;
  withdrawalAge: number;
  strategyGoal: StrategyGoal;
  riskProfile: RiskProfile;
  liquidityPreference: boolean;
  feeSensitivity: boolean;
  incomePreference: boolean;
}

export const DEFAULT_USER_PREFERENCES: UserPreferences = {
  displayName: '김모아',
  annualSalaryKrw: 45_000_000,
  monthlyInvestmentKrw: 500_000,
  investmentYears: 30,
  annualReturnRatePct: 7,
  withdrawalAge: 60,
  strategyGoal: 'retirement',
  riskProfile: 'growth',
  liquidityPreference: true,
  feeSensitivity: true,
  incomePreference: false,
};

const STORAGE_KEY = 'moa-user-preferences-v1';
const listeners = new Set<() => void>();

function clamp(value: unknown, minimum: number, maximum: number, fallback: number) {
  const number = Number(value);
  return Number.isFinite(number) ? Math.min(Math.max(number, minimum), maximum) : fallback;
}

function sanitize(value: unknown): UserPreferences {
  const candidate = value && typeof value === 'object'
    ? value as Partial<UserPreferences>
    : {};
  const strategyGoals: StrategyGoal[] = ['retirement', 'lump_sum', 'cashflow'];
  const riskProfiles: RiskProfile[] = ['conservative', 'balanced', 'growth'];
  const displayName = typeof candidate.displayName === 'string'
    ? candidate.displayName.trim().slice(0, 20)
    : '';

  return {
    displayName: displayName || DEFAULT_USER_PREFERENCES.displayName,
    annualSalaryKrw: Math.round(clamp(
      candidate.annualSalaryKrw,
      0,
      1_000_000_000,
      DEFAULT_USER_PREFERENCES.annualSalaryKrw,
    )),
    monthlyInvestmentKrw: Math.round(clamp(
      candidate.monthlyInvestmentKrw,
      10_000,
      100_000_000,
      DEFAULT_USER_PREFERENCES.monthlyInvestmentKrw,
    )),
    investmentYears: Math.round(clamp(
      candidate.investmentYears,
      3,
      40,
      DEFAULT_USER_PREFERENCES.investmentYears,
    )),
    annualReturnRatePct: clamp(
      candidate.annualReturnRatePct,
      0,
      30,
      DEFAULT_USER_PREFERENCES.annualReturnRatePct,
    ),
    withdrawalAge: Math.round(clamp(
      candidate.withdrawalAge,
      55,
      100,
      DEFAULT_USER_PREFERENCES.withdrawalAge,
    )),
    strategyGoal: strategyGoals.includes(candidate.strategyGoal as StrategyGoal)
      ? candidate.strategyGoal as StrategyGoal
      : DEFAULT_USER_PREFERENCES.strategyGoal,
    riskProfile: riskProfiles.includes(candidate.riskProfile as RiskProfile)
      ? candidate.riskProfile as RiskProfile
      : DEFAULT_USER_PREFERENCES.riskProfile,
    liquidityPreference: typeof candidate.liquidityPreference === 'boolean'
      ? candidate.liquidityPreference
      : DEFAULT_USER_PREFERENCES.liquidityPreference,
    feeSensitivity: typeof candidate.feeSensitivity === 'boolean'
      ? candidate.feeSensitivity
      : DEFAULT_USER_PREFERENCES.feeSensitivity,
    incomePreference: typeof candidate.incomePreference === 'boolean'
      ? candidate.incomePreference
      : DEFAULT_USER_PREFERENCES.incomePreference,
  };
}

function loadPreferences() {
  if (typeof window === 'undefined') return DEFAULT_USER_PREFERENCES;
  try {
    const stored = window.localStorage.getItem(STORAGE_KEY);
    return stored ? sanitize(JSON.parse(stored) as unknown) : DEFAULT_USER_PREFERENCES;
  } catch {
    return DEFAULT_USER_PREFERENCES;
  }
}

let currentPreferences = loadPreferences();

function emitChange() {
  listeners.forEach((listener) => listener());
}

function subscribe(listener: () => void) {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

if (typeof window !== 'undefined') {
  window.addEventListener('storage', (event) => {
    if (event.key !== STORAGE_KEY) return;
    try {
      currentPreferences = event.newValue
        ? sanitize(JSON.parse(event.newValue) as unknown)
        : DEFAULT_USER_PREFERENCES;
    } catch {
      currentPreferences = DEFAULT_USER_PREFERENCES;
    }
    emitChange();
  });
}

export function saveUserPreferences(value: UserPreferences) {
  currentPreferences = sanitize(value);
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(currentPreferences));
  emitChange();
}

export function updateUserPreferences(value: Partial<UserPreferences>) {
  saveUserPreferences({ ...currentPreferences, ...value });
}

export function resetUserPreferences() {
  currentPreferences = DEFAULT_USER_PREFERENCES;
  window.localStorage.removeItem(STORAGE_KEY);
  emitChange();
}

export function useUserPreferences() {
  return useSyncExternalStore(
    subscribe,
    () => currentPreferences,
    () => DEFAULT_USER_PREFERENCES,
  );
}
