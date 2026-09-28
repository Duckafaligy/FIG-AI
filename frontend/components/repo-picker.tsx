"use client";

import { Github, Lock, Search } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { actions, api, type GithubRepo } from "@/lib/api";
import styles from "./repo-picker.module.css";

/**
 * GitHub's Vercel-style import step: the account is already connected (the
 * token sits in a short-lived pending token, see app/oauth.py's picker
 * mode); this lists the repos it can push to, and picking one creates the
 * project -- or, when GitHub can't say where the repo is deployed, hands on
 * to /projects/confirm-url with the repo already attached.
 */
export function RepoPicker() {
  const router = useRouter();
  const [pending, setPending] = useState<string | null>(null);
  const [repos, setRepos] = useState<GithubRepo[] | null>(null);
  const [query, setQuery] = useState("");
  const [busy, setBusy] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    const token = new URLSearchParams(window.location.search).get("pending") ?? "";
    setPending(token);
    if (!token) return;
    api.githubRepos(token).then((result) => {
      if (result.ok) setRepos(result.data.repos);
      else setError(result.error);
    });
  }, []);

  const shown = useMemo(() => {
    const q = query.trim().toLowerCase();
    return (repos ?? []).filter((repo) => !q || repo.full_name.toLowerCase().includes(q));
  }, [repos, query]);

  const pick = async (repo: string) => {
    if (!pending) return;
    setBusy(repo);
    setError("");
    const result = await actions.finishGithubPick(pending, repo);
    if (!result.ok) { setBusy(""); setError(result.error); return; }
    if ("needs_hostname" in result.data) {
      const params = new URLSearchParams({ pending: result.data.pending, platform: "github", repo });
      if (result.data.suggested) params.set("suggested", result.data.suggested);
      router.push(`/projects/confirm-url?${params}`);
      return;
    }
    router.push(`/projects/${encodeURIComponent(result.data.hostname)}`);
  };

  if (pending === "") {
    return <>
      <h1>This link has expired</h1>
      <p>Start the connection again from Add project.</p>
    </>;
  }

  return <>
    <div className="auth-heading">
      <span className="eyebrow">New project · GitHub</span>
      <h2>Import a repository</h2>
      <p>GitHub is connected. Pick the repository behind this website. FIG opens pull requests there and never commits to your default branch.</p>
    </div>
    <label className={styles.search}>
      <Search size={15} aria-hidden />
      <input placeholder="Search repositories" value={query} onChange={(event) => setQuery(event.target.value)}
             aria-label="Search repositories" autoFocus />
    </label>
    {error && <p className="form-message" role="alert">{error}</p>}
    <ul className={styles.list} aria-busy={repos === null}>
      {repos === null && !error && <li className={styles.empty}>Loading your repositories…</li>}
      {repos !== null && shown.length === 0 && (
        <li className={styles.empty}>{repos.length ? "No repository matches that search." : "This account can’t push to any repositories."}</li>
      )}
      {shown.map((repo) => (
        <li key={repo.full_name} className={styles.row}>
          <Github size={16} aria-hidden />
          <div className={styles.name}>
            <strong>{repo.full_name}{repo.private && <Lock size={12} aria-label="Private" />}</strong>
            <small>{repo.homepage.replace(/^https?:\/\//, "").replace(/\/$/, "") || "No website listed"}{repo.pushed_at && ` · pushed ${new Date(repo.pushed_at).toLocaleDateString()}`}</small>
          </div>
          <button className="button button--small" type="button" disabled={!!busy} onClick={() => pick(repo.full_name)}>
            {busy === repo.full_name ? "Importing…" : "Import"}
          </button>
        </li>
      ))}
    </ul>
    <p className={styles.note}>Showing the 100 most recently pushed repositories you can write to.</p>
  </>;
}
