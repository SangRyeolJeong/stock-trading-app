import {
  useEffect,
  useMemo,
  useRef,
  useState,
  type PropsWithChildren,
} from 'react';
import {
  saveUserPreferences,
  setUserPreferencesScope,
  useUserPreferences,
} from '../data/userPreferences';
import { setMarketFavoritesScope } from '../data/marketFavorites';
import { ApiError } from '../services/apiClient';
import { preferencesApi } from '../services/preferencesApi';
import { useAuth } from './authContext';
import {
  PreferencesSyncContext,
  type PreferencesSyncStatus,
} from './preferencesSyncContext';

export function PreferencesSync({ children }: PropsWithChildren) {
  const { isSupabase, session } = useAuth();
  const preferences = useUserPreferences();
  const userId = isSupabase ? session?.user.id ?? null : null;
  const lastSynced = useRef<string | null>(null);
  const [state, setState] = useState<{
    userId: string | null;
    ready: boolean;
    status: PreferencesSyncStatus;
  }>({
    userId: null,
    ready: !userId,
    status: userId ? 'syncing' : 'local',
  });

  useEffect(() => {
    let cancelled = false;
    lastSynced.current = null;

    if (!userId) {
      setMarketFavoritesScope(null);
      setUserPreferencesScope(null);
      return () => {
        cancelled = true;
      };
    }

    setMarketFavoritesScope(userId);
    const scopedPreferences = setUserPreferencesScope(userId);

    const hydrate = async () => {
      try {
        let serverPreferences;
        try {
          serverPreferences = await preferencesApi.get();
        } catch (error) {
          if (!(error instanceof ApiError) || error.status !== 404) throw error;
          serverPreferences = await preferencesApi.save(scopedPreferences);
        }
        if (cancelled) return;
        lastSynced.current = JSON.stringify(serverPreferences);
        saveUserPreferences(serverPreferences);
        setState({ userId, ready: true, status: 'synced' });
      } catch {
        if (cancelled) return;
        setState({ userId, ready: true, status: 'error' });
      }
    };

    void hydrate();
    return () => {
      cancelled = true;
    };
  }, [userId]);

  useEffect(() => {
    if (!userId || state.userId !== userId || !state.ready) return;
    if (lastSynced.current === null) return;
    const serialized = JSON.stringify(preferences);
    if (serialized === lastSynced.current) return;

    const timer = window.setTimeout(() => {
      setState((current) => ({ ...current, status: 'syncing' }));
      void preferencesApi.save(preferences).then((saved) => {
        lastSynced.current = JSON.stringify(saved);
        saveUserPreferences(saved);
        setState((current) => (
          current.userId === userId
            ? { ...current, status: 'synced' }
            : current
        ));
      }).catch(() => {
        setState((current) => (
          current.userId === userId
            ? { ...current, status: 'error' }
            : current
        ));
      });
    }, 600);

    return () => window.clearTimeout(timer);
  }, [preferences, state.ready, state.userId, userId]);

  const contextValue = useMemo(() => state.status, [state.status]);
  if (userId && (state.userId !== userId || !state.ready)) {
    return (
      <main className="auth-screen auth-loading">
        투자 설정을 동기화하고 있어요…
      </main>
    );
  }

  return (
    <PreferencesSyncContext.Provider value={contextValue}>
      {children}
    </PreferencesSyncContext.Provider>
  );
}
