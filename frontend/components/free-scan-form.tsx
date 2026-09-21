"use client";

import { ArrowRight, Loader2 } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";
import { publicScan } from "@/lib/api";

export function FreeScanForm() {
  const [url, setUrl] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  // Free scans are listed in the public library by default; this is the
  // opt-out the API has always supported (`share: false`).
  const [anonymous, setAnonymous] = useState(false);
  const router = useRouter();

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (busy || !url.trim()) return;
    setBusy(true);
    setError("");

    const started = await publicScan.start(url.trim(), !anonymous);
    if (!started.ok) {
      setError(started.error);
      setBusy(false);
      return;
    }
    const { scan_id: scanId, status } = started.data;
    if (status === "done") {
      router.push(`/report/${scanId}`);
      return;
    }

    // Poll until the scan finishes (or fails -- the report page itself
    // renders a clear "couldn't finish" state either way), then land on
    // the report already filled in rather than the "still scanning" state.
    const poll = async () => {
      const result = await publicScan.status(scanId);
      if (result.ok && (result.data.status === "done" || result.data.status === "failed")) {
        router.push(`/report/${scanId}`);
        return;
      }
      setTimeout(poll, 2500);
    };
    setTimeout(poll, 2500);
  };

  return (
    <form className="home-scan-form" onSubmit={submit}>
      <div className="home-scan-input">
        <input
          type="text"
          inputMode="url"
          name="scan-url"
          placeholder="yoursite.com"
          value={url}
          onChange={(event) => setUrl(event.target.value)}
          disabled={busy}
          aria-label="Website URL to scan for free"
          required
        />
        <button className="button" type="submit" disabled={busy}>
          {busy ? (
            <>Scanning<Loader2 size={16} className="home-scan-spin" aria-hidden="true" /></>
          ) : (
            <>Scan it free<ArrowRight size={16} /></>
          )}
        </button>
      </div>
      <label className="home-scan-anon">
        <input type="checkbox" checked={anonymous} onChange={(event) => setAnonymous(event.target.checked)} disabled={busy} />
        Keep this scan anonymous
      </label>
      <p className="home-scan-note">
        Free scans appear in the <Link href="/library">public library</Link> with the site&rsquo;s domain unless you tick this. See our <Link href="/privacy">privacy policy</Link>.
      </p>
      {error && <p className="form-message" role="alert">{error}</p>}
    </form>
  );
}
