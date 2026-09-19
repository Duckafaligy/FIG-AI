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

// createClient() validates its URL eagerly and throws at construction --
// not lazily, not just when a call is made -- so an empty string here
// crashed the build on every page that imports this module (found
// deploying a project with no Supabase env vars set, e.g. a demo
// deployment that has no reason to need them). A syntactically valid
// placeholder keeps construction safe; supabaseConfigured is what actually
// gates every real use, both here and in auth-form.tsx.
export const supabase = createClient(url || "https://placeholder.supabase.co", anonKey || "placeholder", {
  auth: { persistSession: false, autoRefreshToken: false, detectSessionInUrl: false },
});
