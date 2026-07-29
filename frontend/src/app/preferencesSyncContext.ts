import { createContext, useContext } from 'react';

export type PreferencesSyncStatus = 'local' | 'syncing' | 'synced' | 'error';

export const PreferencesSyncContext = createContext<PreferencesSyncStatus>('local');

export function usePreferencesSyncStatus() {
  return useContext(PreferencesSyncContext);
}
