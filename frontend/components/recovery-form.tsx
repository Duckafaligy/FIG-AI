"use client";

import Link from "next/link";
import { ArrowRight, CheckCircle2, Eye, EyeOff, LockKeyhole, Mail } from "lucide-react";
import { FormEvent, useEffect, useRef, useState } from "react";
import { DEMO_MODE } from "@/lib/api";
import { supabase, supabaseConfigured } from "@/lib/supabase";

/**
 * Password recovery, in two halves that share one Supabase flow.
 *
 * 1. `ForgotPasswordForm` asks Supabase to email a link. The answer shown is
 *    always the same whether or not the address has an account, so this page
 *    cannot be used to discover who is registered.
 * 2. `ResetPasswordForm` is where that link lands. Supabase puts the recovery
 *    tokens in the URL *fragment* (`#access_token=...&type=recovery`), so they
 *    never reach any server. The form reads them, then immediately scrubs them
 *    from the address bar and history, sets the new password, and drops the
 *    Supabase session: FIG's own sign-in is a separate, cookie-based session
 *    that this page deliberately does not create. Sign in afterwards as usual.
 *
 * Requires the site's origin (`/reset-password`) to be in Supabase's
 * Authentication -> URL Configuration -> Redirect URLs, or Supabase falls back
 * to the Site URL and the link lands on the wrong page.
 */

const MIN_PASSWORD = 8;

function unavailable(): string | null {
  if (DEMO_MODE) return "This is a demo deployment, so password recovery is disabled here.";
  if (!supabaseConfigured) return "Authentication isn't configured on this deployment.";
  return null;
}

export function ForgotPasswordForm() {
  const [email, setEmail] = useState("");
  const [busy, setBusy] = useState(false);
  const [sent, setSent] = useState(false);
  const [message, setMessage] = useState("");

  useEffect(() => {
    const prefill = new URLSearchParams(window.location.search).get("email");
    if (prefill) setEmail(prefill.slice(0, 254));
  }, []);

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const blocked = unavailable();
    if (blocked) { setMessage(blocked); return; }
    setBusy(true);
    setMessage("");
    try {
      const { error } = await supabase.auth.resetPasswordForEmail(email.trim(), {
        redirectTo: `${window.location.origin}/reset-password`,
      });
      // Rate limits are per project, not per address, so saying so reveals
      // nothing about the account. Everything else gets the same "sent" answer.
      if (error && (error.status === 429 || /rate limit/i.test(error.message))) {
        setMessage("Too many requests right now. Please wait a few minutes and try again.");
        return;
      }
      setSent(true);
    } catch {
      setMessage("We couldn’t reach the sign-in service. Please try again.");
    } finally {
      setBusy(false);
    }
  };

  if (sent) {
    return (
      <div className="auth-form" role="status">
        <div className="auth-heading">
          <span className="eyebrow">Check your email</span>
          <h2>Reset link on its way</h2>
          <p>If an account exists for <strong>{email.trim()}</strong>, we&rsquo;ve sent a link to choose a new password. It can take a few minutes, and it expires after an hour, so check your spam folder if you don&rsquo;t see it.</p>
        </div>
        <p className="auth-switch"><Link href="/signin">Back to sign in</Link></p>
      </div>
    );
  }

  return (
    <form className="auth-form" onSubmit={submit}>
      <div className="auth-heading">
        <span className="eyebrow">Account recovery</span>
        <h2>Forgot your password?</h2>
        <p>Enter the email you signed up with and we&rsquo;ll send you a link to choose a new one.</p>
      </div>
      <label className="auth-field" htmlFor="recover-email">
        <span>Email</span>
        <div className="input-with-icon">
          <Mail size={18} aria-hidden="true" />
          <input id="recover-email" name="email" type="email" required autoComplete="email" placeholder="you@company.com" value={email} onChange={(e) => setEmail(e.target.value)} />
        </div>
      </label>
      <button className="button auth-submit" type="submit" disabled={busy} aria-busy={busy}>
        {busy ? "Sending…" : "Send reset link"}{!busy && <ArrowRight size={18} />}
      </button>
      {message && <p className="form-message" role="status">{message}</p>}
      <p className="auth-switch">Remembered it? <Link href="/signin">Sign in</Link></p>
    </form>
  );
}

type Stage = "checking" | "ready" | "invalid" | "done";

function readFragment(): { stage: Stage; access?: string; refresh?: string; reason?: string } {
  const params = new URLSearchParams(window.location.hash.replace(/^#/, ""));
  // Scrub the tokens from the address bar and history straight away, whatever
  // happens next: they are credentials, and this URL can be bookmarked or shared.
  if (window.location.hash) window.history.replaceState(null, "", window.location.pathname);

  const error = params.get("error_code") || params.get("error");
  if (error) {
    const expired = error === "otp_expired" || /expired/i.test(params.get("error_description") ?? "");
    return { stage: "invalid", reason: expired ? "This link has expired or has already been used." : "This reset link isn’t valid." };
  }
  const access = params.get("access_token");
  const refresh = params.get("refresh_token");
  if (params.get("type") === "recovery" && access && refresh) return { stage: "ready", access, refresh };
  return { stage: "invalid", reason: "This page is opened from the link in your reset email." };
}

export function ResetPasswordForm() {
  const [stage, setStage] = useState<Stage>("checking");
  const [reason, setReason] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [show, setShow] = useState(false);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");

  // Held in memory only, and never rendered or logged.
  const [tokens, setTokens] = useState<{ access: string; refresh: string } | null>(null);

  // readFragment() scrubs the URL, so it must only ever run once: React's
  // development double-invoke of effects would otherwise find the hash gone.
  const parsed = useRef<ReturnType<typeof readFragment> | null>(null);

  useEffect(() => {
    const blocked = unavailable();
    if (blocked) { setReason(blocked); setStage("invalid"); return; }
    if (!parsed.current) parsed.current = readFragment();
    const found = parsed.current;
    setStage(found.stage);
    if (found.reason) setReason(found.reason);
    if (found.access && found.refresh) setTokens({ access: found.access, refresh: found.refresh });
  }, []);

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!tokens) return;
    if (password.length < MIN_PASSWORD) { setMessage(`Use at least ${MIN_PASSWORD} characters.`); return; }
    if (password !== confirm) { setMessage("The two passwords don’t match."); return; }
    setBusy(true);
    setMessage("");
    try {
      const session = await supabase.auth.setSession({ access_token: tokens.access, refresh_token: tokens.refresh });
      if (session.error) {
        setReason("This link has expired or has already been used.");
        setStage("invalid");
        return;
      }
      const { error } = await supabase.auth.updateUser({ password });
      if (error) { setMessage(error.message); return; }
      // Sign-in to FIG itself is our own cookie session; this Supabase session
      // existed only to change the password, so end it here.
      await supabase.auth.signOut({ scope: "local" });
      setTokens(null);
      setStage("done");
    } catch {
      setMessage("We couldn’t reach the sign-in service. Please try again.");
    } finally {
      setBusy(false);
    }
  };

  if (stage === "checking") {
    return <div className="auth-form" role="status" aria-busy="true"><div className="auth-heading"><h2>One moment…</h2></div></div>;
  }

  if (stage === "invalid") {
    return (
      <div className="auth-form" role="alert">
        <div className="auth-heading">
          <span className="eyebrow">Link problem</span>
          <h2>We can&rsquo;t use this link</h2>
          <p>{reason}</p>
        </div>
        <Link className="button auth-submit" href="/forgot-password">Send a new link<ArrowRight size={18} /></Link>
        <p className="auth-switch"><Link href="/signin">Back to sign in</Link></p>
      </div>
    );
  }

  if (stage === "done") {
    return (
      <div className="auth-form" role="status">
        <div className="auth-heading">
          <span className="eyebrow"><CheckCircle2 size={13} /> Password updated</span>
          <h2>You&rsquo;re all set</h2>
          <p>Your password has been changed. Sign in with the new one.</p>
        </div>
        <Link className="button auth-submit" href="/signin">Go to sign in<ArrowRight size={18} /></Link>
      </div>
    );
  }

  return (
    <form className="auth-form" onSubmit={submit}>
      <div className="auth-heading">
        <span className="eyebrow">Account recovery</span>
        <h2>Choose a new password</h2>
        <p>At least {MIN_PASSWORD} characters. Something you don&rsquo;t use anywhere else.</p>
      </div>
      <label className="auth-field" htmlFor="new-password">
        <span>New password</span>
        <div className="input-with-icon input-with-icon--password">
          <LockKeyhole size={18} aria-hidden="true" />
          <input id="new-password" name="password" required minLength={MIN_PASSWORD} type={show ? "text" : "password"} autoComplete="new-password" value={password} onChange={(e) => setPassword(e.target.value)} />
          <button className="password-toggle" type="button" onClick={() => setShow(!show)} aria-label={show ? "Hide password" : "Show password"}>{show ? <EyeOff size={18} /> : <Eye size={18} />}</button>
        </div>
      </label>
      <label className="auth-field" htmlFor="confirm-password">
        <span>Confirm new password</span>
        <div className="input-with-icon input-with-icon--password">
          <LockKeyhole size={18} aria-hidden="true" />
          <input id="confirm-password" name="confirm" required minLength={MIN_PASSWORD} type={show ? "text" : "password"} autoComplete="new-password" value={confirm} onChange={(e) => setConfirm(e.target.value)} />
        </div>
      </label>
      <button className="button auth-submit" type="submit" disabled={busy} aria-busy={busy}>
        {busy ? "Saving…" : "Save new password"}{!busy && <ArrowRight size={18} />}
      </button>
      {message && <p className="form-message" role="alert">{message}</p>}
    </form>
  );
}
