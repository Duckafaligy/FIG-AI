"use client";
import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { actions, apiClient, type ApiMe } from "@/lib/api";

/** Finishes a Google/GitHub sign-in: Supabase returns the access token in the URL
 *  fragment, which is read once, scrubbed from the address bar, and exchanged for
 *  FIG's own session cookie (same /api/session call as email sign-in). */
export function OAuthCallback() {
  const [error, setError] = useState("");
  const started = useRef(false);

  useEffect(() => {
    // Once only: the token is single-use and the URL is scrubbed on first read.
    if (started.current) return;
    started.current = true;
    const hash = new URLSearchParams(window.location.hash.slice(1));
    const query = new URLSearchParams(window.location.search);
    if (window.location.hash || window.location.search) window.history.replaceState(null, "", window.location.pathname);

    const token = hash.get("access_token");
    const failure = hash.get("error_description") || query.get("error_description");
    if (!token) {
      setError(failure ? `Sign-in didn’t finish: ${failure}` : "Sign-in didn’t finish. Please try again.");
      return;
    }
    (async () => {
      const established = await actions.signIn(token);
      if (!established.ok) {
        setError(established.status === 401 ? "Your sign-in expired. Please try again." : "You were signed in, but FIG couldn’t open your workspace. Please try again.");
        return;
      }
      const me = await apiClient<ApiMe>("/api/me");
      if (!me.ok || !me.data.signed_in) {
        setError("FIG couldn’t confirm your browser session. Check that cookies are allowed for this site, then try again.");
        return;
      }
      window.location.replace("/projects");
    })();
  }, []);

  return (
    <div className="auth-simple-card oauth-status">
      {error ? <>
        <h1 className="af-title">That didn’t work</h1>
        <p className="af-message" role="alert">{error}</p>
        <p className="af-switch"><Link href="/signin">Back to sign in</Link></p>
      </> : <>
        <h1 className="af-title">Signing you in…</h1>
        <p className="af-switch" role="status">Opening your workspace.</p>
      </>}
    </div>
  );
}
