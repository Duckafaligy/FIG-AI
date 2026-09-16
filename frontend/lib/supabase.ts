/**
 * Browser-side Supabase client, used only to sign in/up and get an access
 * token. The token is handed to the backend once (`actions.signIn` in
 * lib/api.ts, which posts to `/api/session`) and then dropped — the
 * long-lived session is our own HttpOnly cookie, not anything Supabase
 * hands out, so this client never needs to persist or refresh a session
 * itself.
 */
import { createClient } from "@supabase/supabase-js";

const url = process.env.NEXT_PUBLIC_SUPABASE_URL ?? "";
const anonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY ?? "";

export const supabaseConfigured = Boolean(url && anonKey);

export const supabase = createClient(url, anonKey, {
  auth: { persistSession: false, autoRefreshToken: false, detectSessionInUrl: false },
});
