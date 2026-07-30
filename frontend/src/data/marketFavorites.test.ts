import { beforeEach, describe, expect, it } from 'vitest';
import {
  DEFAULT_MARKET_FAVORITES,
  resetMarketFavorites,
  saveMarketFavorites,
  setMarketFavoritesScope,
  toggleMarketFavorite,
} from './marketFavorites';

describe('market favorite storage', () => {
  beforeEach(() => {
    setMarketFavoritesScope(null);
    resetMarketFavorites();
    window.localStorage.clear();
  });

  it('normalizes, validates, and deduplicates symbols', () => {
    saveMarketFavorites([' aapl ', 'AAPL', '005930', '', 'invalid symbol']);

    expect(JSON.parse(window.localStorage.getItem('moa-market-favorites') ?? '[]')).toEqual([
      'AAPL',
      '005930',
    ]);
  });

  it('adds and removes a favorite', () => {
    saveMarketFavorites(['QQQM']);

    toggleMarketFavorite(' nvda ');
    expect(JSON.parse(window.localStorage.getItem('moa-market-favorites') ?? '[]')).toEqual([
      'QQQM',
      'NVDA',
    ]);

    toggleMarketFavorite('QQQM');
    expect(JSON.parse(window.localStorage.getItem('moa-market-favorites') ?? '[]')).toEqual([
      'NVDA',
    ]);
  });

  it('keeps authenticated users in separate local watchlists', () => {
    setMarketFavoritesScope('user-a');
    saveMarketFavorites(['AAPL']);

    expect(setMarketFavoritesScope('user-b')).toEqual(DEFAULT_MARKET_FAVORITES);
    saveMarketFavorites(['005930']);

    expect(setMarketFavoritesScope('user-a')).toEqual(['AAPL']);
    expect(setMarketFavoritesScope('user-b')).toEqual(['005930']);
  });

  it('restores the default watchlist', () => {
    saveMarketFavorites([]);
    resetMarketFavorites();

    expect(setMarketFavoritesScope('temporary-user')).toEqual(DEFAULT_MARKET_FAVORITES);
    expect(setMarketFavoritesScope(null)).toEqual(DEFAULT_MARKET_FAVORITES);
  });
});
