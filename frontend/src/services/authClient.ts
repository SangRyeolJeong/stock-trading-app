import type { SupabaseClient } from '@supabase/supabase-js';

export const AUTH_MODE = import.meta.env.VITE_AUTH_MODE === 'supabase'
  ? 'supabase'
  : 'demo';

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
const supabasePublishableKey = import.meta.env.VITE_SUPABASE_PUBLISHABLE_KEY;

export const AUTH_CONFIGURATION_ERROR = AUTH_MODE === 'supabase' && (
  !supabaseUrl || !supabasePublishableKey
)
  ? 'Supabase 인증에는 VITE_SUPABASE_URL과 VITE_SUPABASE_PUBLISHABLE_KEY가 필요합니다.'
  : null;

let clientPromise: Promise<SupabaseClient | null> | null = null;

export function getSupabaseClient() {
  if (AUTH_MODE !== 'supabase' || AUTH_CONFIGURATION_ERROR) {
    return Promise.resolve(null);
  }
  clientPromise ??= import('@supabase/supabase-js').then(({ createClient }) => (
    createClient(supabaseUrl!, supabasePublishableKey!)
  ));
  return clientPromise;
}

export async function getAccessToken() {
  const client = await getSupabaseClient();
  if (!client) return null;
  const { data, error } = await client.auth.getSession();
  if (error) return null;
  return data.session?.access_token ?? null;
}
