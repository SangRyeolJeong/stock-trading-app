import type { Session } from '@supabase/supabase-js';
import { createContext, useContext } from 'react';

export interface AuthContextValue {
  session: Session | null;
  isSupabase: boolean;
  userEmail: string | null;
  signOut: () => Promise<void>;
}

export const AuthContext = createContext<AuthContextValue | null>(null);

export function useAuth() {
  const value = useContext(AuthContext);
  if (!value) throw new Error('useAuth must be used inside AuthProvider');
  return value;
}
