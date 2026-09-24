"use client";

import { ArrowRight } from "lucide-react";
import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { actions } from "@/lib/api";

/**
 * The one extra step for the two platforms that can't tell FIG their own
 * live domain: GitHub (no GitHub Pages custom domain configured) and Wix
 * (its Site Properties API has no URL field at all -- see app/oauth.py's
 * "creating a project from a platform that can't tell us its own domain").
 * The platform is already connected by the time a browser lands here; this
 * only creates the project and attaches that connection.
 */
export function ConfirmUrlForm() {
  const router = useRouter();
  const [pending, setPending] = useState("");
  const [platform, setPlatform] = useState("");
  const [hostname, setHostname] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    setPending(params.get("pending") ?? "");
    setPlatform(params.get("platform") ?? "");
  }, []);

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setBusy(true);
    setError("");
    const result = await actions.finishOauthCreate(pending, hostname.trim());
    setBusy(false);
    if (!result.ok) { setError(result.error); return; }
    router.push(`/projects/${encodeURIComponent(result.data.hostname)}`);
  };

  const platformLabel = platform ? platform[0].toUpperCase() + platform.slice(1) : "That platform";

  if (!pending) {
    return <>
      <h1>This link has expired</h1>
      <p>Start the connection again from Add project.</p>
    </>;
  }

  return <>
    <h1>One more thing</h1>
    <p>{platformLabel} is connected, but it can&rsquo;t tell FIG this site&rsquo;s live URL on its own. What&rsquo;s it deployed at?</p>
    <form onSubmit={submit} className="auth-fields">
      <label className="auth-field" htmlFor="confirm-hostname">
        <span>Website URL</span>
        <input id="confirm-hostname" required placeholder="yoursite.com" autoFocus
              value={hostname} onChange={(event) => setHostname(event.target.value)} />
      </label>
      {error && <p className="form-message" role="alert">{error}</p>}
      <button className="button" type="submit" disabled={busy}>
        {busy ? "Creating…" : "Create project"}{!busy && <ArrowRight size={16} />}
      </button>
    </form>
  </>;
}
