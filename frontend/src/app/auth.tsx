import type { Session } from '@supabase/supabase-js';
import { useQueryClient } from '@tanstack/react-query';
import {
  useEffect,
  useMemo,
  useState,
  type PropsWithChildren,
} from 'react';
import { LoginPage } from '../pages/LoginPage';
import {
  AUTH_CONFIGURATION_ERROR,
  AUTH_MODE,
  getSupabaseClient,
} from '../services/authClient';
import { AuthContext, type AuthContextValue } from './authContext';

export function AuthProvider({ children }: PropsWithChildren) {
  const queryClient = useQueryClient();
  const [authState, setAuthState] = useState<{
    loading: boolean;
    session: Session | null;
  }>({
    loading: AUTH_MODE === 'supabase' && !AUTH_CONFIGURATION_ERROR,
    session: null,
  });

  useEffect(() => {
    if (AUTH_MODE !== 'supabase' || AUTH_CONFIGURATION_ERROR) return;
    let disposed = false;
    let unsubscribe: (() => void) | undefined;
    void getSupabaseClient().then((client) => {
      if (!client || disposed) return;
      const { data: { subscription } } = client.auth.onAuthStateChange(
        (_event, session) => {
          setAuthState({ loading: false, session });
          queryClient.clear();
        },
      );
      unsubscribe = () => subscription.unsubscribe();
    });
    return () => {
      disposed = true;
      unsubscribe?.();
    };
  }, [queryClient]);

  const contextValue = useMemo<AuthContextValue>(() => ({
    session: authState.session,
    isSupabase: AUTH_MODE === 'supabase',
    userEmail: authState.session?.user.email ?? null,
    signOut: async () => {
      const client = await getSupabaseClient();
      if (!client) return;
      const { error } = await client.auth.signOut({ scope: 'local' });
      if (error) throw error;
    },
  }), [authState.session]);

  let content = children;
  if (AUTH_CONFIGURATION_ERROR) {
    content = (
      <main className="auth-screen">
        <section className="auth-card">
          <p className="eyebrow">AUTH CONFIGURATION</p>
          <h1>인증 설정을 확인해 주세요</h1>
          <p>{AUTH_CONFIGURATION_ERROR}</p>
        </section>
      </main>
    );
  } else if (authState.loading) {
    content = <main className="auth-screen auth-loading">로그인 상태를 확인하고 있어요…</main>;
  } else if (AUTH_MODE === 'supabase' && !authState.session) {
    content = <LoginPage />;
  }

  return (
    <AuthContext.Provider value={contextValue}>
      {content}
    </AuthContext.Provider>
  );
}
