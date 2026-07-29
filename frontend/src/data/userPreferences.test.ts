import { beforeEach, describe, expect, it } from 'vitest';
import {
  DEFAULT_USER_PREFERENCES,
  resetUserPreferences,
  saveUserPreferences,
  setUserPreferencesScope,
} from './userPreferences';

describe('user preference storage scopes', () => {
  beforeEach(() => {
    setUserPreferencesScope(null);
    resetUserPreferences();
    window.localStorage.clear();
  });

  it('keeps authenticated users in separate local cache keys', () => {
    setUserPreferencesScope('user-a');
    saveUserPreferences({
      ...DEFAULT_USER_PREFERENCES,
      displayName: '사용자 A',
    });

    const userB = setUserPreferencesScope('user-b');
    expect(userB.displayName).toBe(DEFAULT_USER_PREFERENCES.displayName);
    saveUserPreferences({
      ...DEFAULT_USER_PREFERENCES,
      displayName: '사용자 B',
    });

    expect(setUserPreferencesScope('user-a').displayName).toBe('사용자 A');
    expect(setUserPreferencesScope('user-b').displayName).toBe('사용자 B');
  });

  it('keeps demo preferences separate from authenticated users', () => {
    saveUserPreferences({
      ...DEFAULT_USER_PREFERENCES,
      displayName: '데모 사용자',
    });

    expect(setUserPreferencesScope('user-a').displayName).toBe(
      DEFAULT_USER_PREFERENCES.displayName,
    );
    expect(setUserPreferencesScope(null).displayName).toBe('데모 사용자');
  });
});
