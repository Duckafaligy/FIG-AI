"use client";
import Link from "next/link";
import { FormEvent, useEffect, useRef, useState } from "react";
import { actions, apiClient, type ApiMe } from "@/lib/api";
import { supabase } from "@/lib/supabase";

type Step = { kind: "working" } | { kind: "password"; email: string; token: string } | { kind: "error"; message: string };

/** Finishes a Google/GitHub sign-in. Supabase returns the tokens in the URL
 *  fragment; they are read once and scrubbed from the address bar. A first-time
 *  OAuth user is asked (once) to set a password so they can also sign in with
 *  email; then the access token is exchanged for FIG's own session cookie via the
 *  same /api/session call as email sign-in (which creates the workspace). */
export function OAuthCallback() {
  const [step, setStep] = useState<Step>({ kind: "working" });
  const [busy, setBusy] = useState(false);
  const started = useRef(false);

  const openWorkspace = async (token: string) => {
    setStep({ kind: "working" });
    const established = await actions.signIn(token);
    if (!established.ok) {
      setStep({ kind: "error", message: established.status === 401 ? "Your sign-in expired. Please try again." : "You were signed in, but FIG couldn’t open your workspace. Please try again." });
      return;
    }
    const me = await apiClient<ApiMe>("/api/me");
    if (!me.ok || !me.data.signed_in) {
      setStep({ kind: "error", message: "FIG couldn’t confirm your browser session. Check that cookies are allowed for this site, then try again." });
      return;
    }
    window.location.replace("/projects");
  };

  useEffect(() => {
    // Once only: the token is single-use and the URL is scrubbed on first read.
    if (started.current) return;
    started.current = true;
    const hash = new URLSearchParams(window.location.hash.slice(1));
    const query = new URLSearchParams(window.location.search);
    if (window.location.hash || window.location.search) window.history.replaceState(null, "", window.location.pathname);

    const token = hash.get("access_token");
    const refresh = hash.get("refresh_token");
    const failure = hash.get("error_description") || query.get("error_description");
    if (!token || !refresh) {
      setStep({ kind: "error", message: failure ? `Sign-in didn’t finish: ${failure}` : "Sign-in didn’t finish. Please try again." });
      return;
    }
    (async () => {
      const { data, error } = await supabase.auth.setSession({ access_token: token, refresh_token: refresh });
      const user = data.user;
      if (error || !user) {
        setStep({ kind: "error", message: "Your sign-in expired. Please try again." });
        return;
      }
      const hasPassword = user.identities?.some(i => i.provider === "email");
      if (!hasPassword && !user.user_metadata?.password_prompted) {
        setStep({ kind: "password", email: user.email ?? "", token });
        return;
      }
      await openWorkspace(token);
    })();
  }, []);

  const savePassword = async (event: FormEvent<HTMLFormElement>, token: string) => {
    event.preventDefault();
    const password = String(new FormData(event.currentTarget).get("password") ?? "");
    setBusy(true);
    const { error } = await supabase.auth.updateUser({ password, data: { password_prompted: true } });
    setBusy(false);
    if (error) { setStep({ kind: "error", message: "That password couldn’t be saved. You can set one later from the sign-in page with Forgot password." }); return; }
    await openWorkspace(token);
  };
  const skip = async (token: string) => {
    setBusy(true);
    await supabase.auth.updateUser({ data: { password_prompted: true } });
    await openWorkspace(token);
  };

  if (step.kind === "password") {
    return (
      <form className="auth-simple-card af" onSubmit={e => savePassword(e, step.token)}>
        <h1 className="af-title">Set a password</h1>
        <p className="af-switch af-left">Your account is ready. Add a password so you can also sign in with {step.email ? <strong>{step.email}</strong> : "your email"}.</p>
        <input type="email" name="username" autoComplete="username" value={step.email} readOnly hidden />
        <label className="af-field" htmlFor="new-password"><span>Password</span>
          <input id="new-password" name="password" type="password" required minLength={8} autoComplete="new-password" placeholder="At least 8 characters" />
        </label>
        <button className="button af-submit" type="submit" disabled={busy}>{busy ? "Saving…" : "Save and continue"}</button>
        <button className="af-skip" type="button" disabled={busy} onClick={() => skip(step.token)}>Skip for now</button>
      </form>
    );
  }
  return (
    <div className="auth-simple-card oauth-status">
      {step.kind === "error" ? <>
        <h1 className="af-title">That didn’t work</h1>
        <p className="af-message" role="alert">{step.message}</p>
        <p className="af-switch"><Link href="/signin">Back to sign in</Link></p>
      </> : <>
        <h1 className="af-title">Signing you in…</h1>
        <p className="af-switch" role="status">Opening your workspace.</p>
      </>}
    </div>
  );
}
