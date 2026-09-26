"use client";

import Link from "next/link";
import Image from "next/image";
import { Eye, EyeOff } from "lucide-react";
import { FormEvent, useEffect, useRef, useState } from "react";
import { siGithub } from "simple-icons";
import { actions, apiClient, DEMO_MODE, type ApiMe } from "@/lib/api";
import { supabase, supabaseConfigured } from "@/lib/supabase";

function ProviderMark({ icon }: { icon: { path: string; title: string } }) {
  return <svg className="provider-mark" aria-hidden="true" viewBox="0 0 24 24"><path d={icon.path} fill="currentColor" /></svg>;
}

/**
 * Google/GitHub sign-in through Supabase. A button only appears once its
 * provider is switched on in Supabase and listed here (Vercel env), so none
 * can promise a sign-in that would fail. Example: NEXT_PUBLIC_OAUTH_PROVIDERS=google,github
 */
const OAUTH_PROVIDERS = (process.env.NEXT_PUBLIC_OAUTH_PROVIDERS ?? "")
  .split(",").map(s => s.trim()).filter((s): s is "google" | "github" => s === "google" || s === "github");

export function AuthForm({ mode }: { mode: "signin" | "signup" }) {
  const [message, setMessage] = useState("");
  const [email, setEmail] = useState("");
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    setEmail((params.get("email") ?? "").slice(0, 254));
  }, []);
  const [showPassword, setShowPassword] = useState(false);
  const [busy, setBusy] = useState(false);
  const signup = mode === "signup";
  const pendingSession = useRef<{ token: string; company: string } | null>(null);
  const [canRetrySession, setCanRetrySession] = useState(false);
  const establishSession = async (token: string, company: string) => {
    pendingSession.current = { token, company };
    const established = await actions.signIn(token, company);
    if (!established.ok) {
      setCanRetrySession(established.status !== 401);
      if (established.status === 401) pendingSession.current = null;
      setMessage(established.status === 401 ? "Your sign-in expired. Please sign in again." : "Your account was authenticated, but FIG couldn’t open your workspace. Retry the connection below; you don’t need to create another account.");
      return;
    }
    const session = await apiClient<ApiMe>("/api/me");
    if (!session.ok || !session.data.signed_in) {
      setCanRetrySession(true);
      setMessage("FIG couldn’t confirm your browser session. Retry the connection. If this continues, check that cookies are allowed for this site.");
      return;
    }
    pendingSession.current = null;
    setCanRetrySession(false);
    // A full navigation avoids reusing a prefetched, signed-out App Router tree.
    window.location.replace("/projects");
  };
  const retrySession = async () => {
    if (busy || !pendingSession.current) return;
    setBusy(true);
    setMessage("");
    try { await establishSession(pendingSession.current.token, pendingSession.current.company); }
    catch { setMessage("The connection was interrupted. Please retry."); }
    finally { setBusy(false); }
  };

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (busy) return;
    if (DEMO_MODE) {
      setMessage("This is a demo deployment — sign-in is disabled here so it can never touch a real account.");
      return;
    }
    if (!supabaseConfigured) {
      setMessage("Authentication isn't configured on this deployment (missing Supabase env vars).");
      return;
    }
    const form = new FormData(event.currentTarget);
    const email = String(form.get("email") ?? "").trim();
    const password = String(form.get("password") ?? "");
    const company = String(form.get("company") ?? "").trim();
    const fullName = String(form.get("full-name") ?? "").trim();

    setBusy(true);
    setMessage("");
    setCanRetrySession(false);
    pendingSession.current = null;
    try {
      const { data, error } = signup
        ? await supabase.auth.signUp({
            email, password,
            // Without this the confirmation link goes to Supabase's Site URL,
            // which was still localhost:3000. It must also be allow-listed in
            // Supabase -> Authentication -> URL Configuration -> Redirect URLs.
            options: { data: { full_name: fullName, company }, emailRedirectTo: `${window.location.origin}/signin` },
          })
        : await supabase.auth.signInWithPassword({ email, password });

      if (error) {
        setMessage(error.code === "invalid_credentials" ? "The email or password wasn’t accepted. Check your email address or use Forgot password to reset it."
          : error.code === "email_not_confirmed" ? "Confirm your email address before signing in. Check your inbox and spam folder for the confirmation email."
          : error.status === 429 ? "Too many attempts. Please wait a few minutes before trying again."
          : error.message);
        return;
      }
      if (!data.session) {
        // Signup with email confirmation required: Supabase creates the user
        // but withholds a session until the link in that email is clicked.
        setMessage("Check your email to confirm your account, then sign in.");
        return;
      }

      await establishSession(data.session.access_token, company);
    } catch {
      setMessage("We couldn’t reach the sign-in service. Please try again.");
    } finally {
      setBusy(false);
    }
  };

  const continueWith = async (provider: "google" | "github") => {
    if (DEMO_MODE) { setMessage("This is a demo deployment — sign-in is disabled here so it can never touch a real account."); return; }
    if (!supabaseConfigured) { setMessage("Authentication isn't configured on this deployment (missing Supabase env vars)."); return; }
    setBusy(true);
    setMessage("");
    const { error } = await supabase.auth.signInWithOAuth({ provider, options: { redirectTo: `${window.location.origin}/auth/callback` } });
    if (error) { setMessage(`Couldn’t start ${provider === "google" ? "Google" : "GitHub"} sign-in. Please try again.`); setBusy(false); }
  };

  return (
    <form className={`af af--${mode}`} onSubmit={submit}>
      <h2 className="af-title">{signup ? "Create your account" : "Sign in"}</h2>

      {signup && <label className="af-field" htmlFor="full-name"><span>Full name</span><input id="full-name" name="full-name" required autoComplete="name" placeholder="Your name" /></label>}
      {signup && <label className="af-field" htmlFor="company"><span>Company name</span><input id="company" name="company" required autoComplete="organization" placeholder="LaunchVault" /></label>}
      <label className="af-field" htmlFor="email"><span>Email</span><input id="email" name="email" value={email} onChange={(event) => setEmail(event.target.value)} required type="email" autoComplete="email" placeholder="you@company.com" /></label>
      <div className="af-field">
        <div className="af-label-row"><label htmlFor="password">Password</label>{!signup && <Link href="/forgot-password">Forgot password?</Link>}</div>
        <div className="af-password">
          <input id="password" name="password" required minLength={signup ? 8 : undefined} type={showPassword ? "text" : "password"} autoComplete={signup ? "new-password" : "current-password"} placeholder={signup ? "At least 8 characters" : "Your password"} />
          <button type="button" onClick={() => setShowPassword(!showPassword)} aria-label={showPassword ? "Hide password" : "Show password"}>{showPassword ? <EyeOff size={17} /> : <Eye size={17} />}</button>
        </div>
      </div>

      {signup && <div className="af-check"><input id="terms" required type="checkbox" aria-label="Agree to the terms and privacy policy, and confirm you are at least 13" /><div><label htmlFor="terms">I&rsquo;m at least 13 and I agree to the </label><Link href="/terms" target="_blank">Terms &amp; Conditions</Link> and <Link href="/privacy" target="_blank">Privacy Policy</Link>.</div></div>}
      <button className="button af-submit" type="submit" disabled={busy} aria-busy={busy}>{busy ? "Please wait…" : signup ? "Start free trial" : "Sign in"}</button>

      {OAUTH_PROVIDERS.length > 0 && (
        <div className="af-oauth">
          <div className="af-or"><span>or</span></div>
          {OAUTH_PROVIDERS.includes("google") && <button className="af-oauth-button" type="button" disabled={busy} onClick={() => continueWith("google")}><Image src="/brands/google-g.png" width={18} height={18} alt="" unoptimized />Continue with Google</button>}
          {OAUTH_PROVIDERS.includes("github") && <button className="af-oauth-button" type="button" disabled={busy} onClick={() => continueWith("github")}><ProviderMark icon={siGithub} />Continue with GitHub</button>}
          <p className="af-oauth-terms">By continuing, you confirm you&rsquo;re at least 13 and agree to the <Link href="/terms" target="_blank">Terms &amp; Conditions</Link> and <Link href="/privacy" target="_blank">Privacy Policy</Link>.</p>
        </div>
      )}
      {message && <p className="af-message" role="status">{message}</p>}
      {canRetrySession && <button className="secondary-button" type="button" disabled={busy} onClick={retrySession}>Retry workspace connection</button>}
      <p className="af-switch">{signup ? "Already have an account?" : "No account yet?"} <Link href={signup ? "/signin" : "/signup"}>{signup ? "Sign in" : "Sign up"}</Link></p>
    </form>
  );
}
