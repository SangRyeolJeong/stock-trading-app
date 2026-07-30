import { useSyncExternalStore } from 'react';

export const DEFAULT_MARKET_FAVORITES = ['QQQM', '005930', 'AAPL', 'NVDA', '360750'];

const STORAGE_KEY_PREFIX = 'moa-market-favorites';
const MAX_FAVORITES = 50;
const SYMBOL_PATTERN = /^[A-Z0-9][A-Z0-9.-]{0,14}$/;
const listeners = new Set<() => void>();
let activeStorageKey = STORAGE_KEY_PREFIX;

function sanitize(value: unknown) {
  if (!Array.isArray(value)) return DEFAULT_MARKET_FAVORITES;

  return [...new Set(
    value
      .filter((item): item is string => typeof item === 'string')
      .map((item) => item.trim().toUpperCase())
      .filter((item) => SYMBOL_PATTERN.test(item)),
  )].slice(0, MAX_FAVORITES);
}

function loadFavorites(storageKey = activeStorageKey) {
  if (typeof window === 'undefined') return DEFAULT_MARKET_FAVORITES;
  try {
    const stored = window.localStorage.getItem(storageKey);
    return stored ? sanitize(JSON.parse(stored) as unknown) : DEFAULT_MARKET_FAVORITES;
  } catch {
    return DEFAULT_MARKET_FAVORITES;
  }
}

let currentFavorites = loadFavorites();

function emitChange() {
  listeners.forEach((listener) => listener());
}

function subscribe(listener: () => void) {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

if (typeof window !== 'undefined') {
  window.addEventListener('storage', (event) => {
    if (event.key !== activeStorageKey) return;
    try {
      currentFavorites = event.newValue
        ? sanitize(JSON.parse(event.newValue) as unknown)
        : DEFAULT_MARKET_FAVORITES;
    } catch {
      currentFavorites = DEFAULT_MARKET_FAVORITES;
    }
    emitChange();
  });
}

export function saveMarketFavorites(value: string[]) {
  currentFavorites = sanitize(value);
  window.localStorage.setItem(activeStorageKey, JSON.stringify(currentFavorites));
  emitChange();
}

export function toggleMarketFavorite(symbol: string) {
  const normalized = symbol.trim().toUpperCase();
  if (!SYMBOL_PATTERN.test(normalized)) return;
  saveMarketFavorites(
    currentFavorites.includes(normalized)
      ? currentFavorites.filter((item) => item !== normalized)
      : [...currentFavorites, normalized],
  );
}

export function resetMarketFavorites() {
  currentFavorites = DEFAULT_MARKET_FAVORITES;
  window.localStorage.removeItem(activeStorageKey);
  emitChange();
}

export function setMarketFavoritesScope(userId: string | null) {
  const nextStorageKey = userId
    ? `${STORAGE_KEY_PREFIX}:${encodeURIComponent(userId)}`
    : STORAGE_KEY_PREFIX;
  if (nextStorageKey === activeStorageKey) return currentFavorites;
  activeStorageKey = nextStorageKey;
  currentFavorites = loadFavorites(nextStorageKey);
  emitChange();
  return currentFavorites;
}

export function useMarketFavorites() {
  return useSyncExternalStore(
    subscribe,
    () => currentFavorites,
    () => DEFAULT_MARKET_FAVORITES,
  );
}
