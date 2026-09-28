"use client";

import Link from "next/link";
import { useCallback, useEffect, useRef, useState } from "react";
import { actions, api, type ApiChangeRow, type ApiChangesPage } from "@/lib/api";
import styles from "./project-page.module.css";

type Action = "approve" | "reject" | "publish" | "revert";
type Tab = "proposed" | "approved" | "failed" | "published";

const TABS: [Tab, string][] = [["proposed", "Proposed"], ["approved", "Approved"], ["failed", "Failed"], ["published", "Published"]];
const LAYER_LABEL: Record<string, string> = { craft: "Craft", structure: "Structure", search: "Search", answers: "Answers" };
const STATE_CLASS: Record<string, string> = { proposed: "answers", approved: "structure", published: "search", failed: "failed" };
const HOW: Record<string, string> = {
  github: "Opens a pull request on the connected repository. Nothing reaches the live site until you merge it.",
  wordpress: "Writes to WordPress through the connected account.",
  shopify: "Writes to Shopify through the connected store.",
  webflow: "Writes to Webflow through the connected site.",
  wix: "Writes to Wix through the connected site.",
};
const NUMBER = ["No", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine", "Ten"];

function pathOf(row: ApiChangeRow): string {
  if (!row.page) return "whole site";
  try { return new URL(row.page).pathname || "/"; } catch { return row.page; }
}

function Change({ row, busy, onAction }: { row: ApiChangeRow; busy: boolean; onAction: (id: string, a: Action) => void }) {
  const act = (a: Action) => () => onAction(row.id, a);
  const published = row.state === "published";
  return <article className={`${styles.change} ${row.state === "proposed" ? styles.changeWaiting : ""}`}>
    <div className={styles.changeHead}>
      <span className={`${styles.layerTag} ${styles[STATE_CLASS[row.state]] ?? ""}`}>{row.state[0].toUpperCase() + row.state.slice(1)}</span>
      {row.layer && <span className={`${styles.layerTag} ${styles[row.layer] ?? ""}`}>{LAYER_LABEL[row.layer] ?? row.layer}</span>}
      <strong>{row.title}</strong>
      <code>{pathOf(row)}</code>
    </div>
    {(row.before || row.after) && <div className={styles.beforeAfter}>
      <div className={published ? styles.beforeQuiet : styles.before}><span>{published ? "Before" : "Now"}{row.before ? ` · ${row.before.length} characters` : ""}</span><p>{row.before || "Nothing there yet."}</p></div>
      <div className={styles.after}><span>{published ? "Live" : "After"}{row.after ? ` · ${row.after.length} characters` : ""}</span><p>{row.after || "Written when you approve it."}</p></div>
    </div>}
    {row.detail && !row.before && !row.after && <p className={styles.bodyText}>{row.detail}</p>}
    {row.state === "failed" && row.error && <p className="form-message" role="alert">{row.error}</p>}
    <div className={styles.changeFoot}>
      <span>{row.platform ? HOW[row.platform] ?? `Writes through ${row.platform}.` : "No site connection yet. Connect one under Settings to publish."}</span>
      {row.state === "proposed" && <>
        <button type="button" className={styles.ghost} disabled={busy} onClick={act("reject")}>Reject</button>
        <button type="button" className={styles.primarySmall} disabled={busy} onClick={act("approve")}>Approve</button>
      </>}
      {row.state === "approved" && <>
        <button type="button" className={styles.ghost} disabled={busy} onClick={act("reject")}>Reject</button>
        <button type="button" className={styles.primarySmall} disabled={busy || !row.can_publish} title={row.can_publish ? undefined : "Connect a site under Settings first"} onClick={act("publish")}>
          {row.platform === "github" ? "Open pull request" : "Publish"}
        </button>
      </>}
      {row.state === "failed" && <>
        <button type="button" className={styles.ghost} disabled={busy} onClick={act("reject")}>Reject</button>
        <button type="button" className={styles.primarySmall} disabled={busy} onClick={act("approve")} title="Sends it back to Approved so it can be retried">Retry</button>
      </>}
      {published && <button type="button" className={styles.ghost} disabled={busy} onClick={act("revert")}>Revert</button>}
    </div>
  </article>;
}

/** One project's publish queue (Paper 2c.6). FIG proposes, a person
 *  approves, and every published change keeps its before-state. */
export function PublishQueue({ projectId }: { projectId: string }) {
  const [data, setData] = useState<ApiChangesPage | null>(null);
  const [error, setError] = useState("");
  const [tab, setTab] = useState<Tab>("proposed");
  const [proposing, setProposing] = useState(false);
  const [busyId, setBusyId] = useState<string | null>(null);
  const [actionError, setActionError] = useState("");
  const request = useRef(0);
  const base = `/projects/${encodeURIComponent(projectId)}`;

  const load = useCallback(async () => {
    const id = ++request.current;
    const result = await api.changes(projectId);
    if (id !== request.current) return;
    if (!result.ok) { setError(result.status === 401 ? "Your session expired. Please sign in again." : result.error); return; }
    setData(result.data); setError("");
  }, [projectId]);
  useEffect(() => { load(); }, [load]);

  const propose = async () => {
    setProposing(true);
    setActionError("");
    const result = await actions.proposeChanges(projectId);
    setProposing(false);
    if (!result.ok) { setActionError(result.error); return; }
    setTab("proposed");
    load();
  };

  const onAction = async (id: string, action: Action) => {
    setBusyId(id);
    setActionError("");
    const result = await actions.changeAction(id, action);
    setBusyId(null);
    if (!result.ok) { setActionError(result.error); return; }
    load();
  };

  if (error) return <p className="form-message" role="alert">{error}</p>;
  if (!data) return <p className={styles.empty} role="status">Loading the publish queue…</p>;

  const waiting = data.counts.proposed ?? 0;
  const rows = data.rows.filter((r) => r.state === tab);
  const closed = data.rows.filter((r) => r.state === "rejected" || r.state === "reverted");
  const blocked = data.not_queueable ?? [];

  return <div className={styles.page}>
    <header className={styles.head}>
      <div>
        <span className={styles.eyebrow}>{projectId} · Publish</span>
        <h1>{waiting ? `${NUMBER[waiting] ?? waiting} change${waiting === 1 ? " is" : "s are"} waiting for you.` : "Nothing is waiting for you."}</h1>
        <p>FIG proposes the change and keeps the old text, you approve it, and it goes out through the connected site. Every published change can be reverted.</p>
      </div>
      <div className={styles.headActions}>
        <button type="button" className={styles.primary} disabled={proposing} onClick={propose}>{proposing ? "Checking…" : "Check for fixes"}</button>
      </div>
    </header>

    {data.connected === 0 && <div className={styles.banner} role="status">
      <div><strong>No site connection yet</strong><span>You can review and approve here, but nothing can be published until this project is connected to its CMS or repository.</span></div>
      <Link className={styles.bannerAction} href={`${base}/settings`}>Connect</Link>
    </div>}
    {actionError && <p className="form-message" role="alert">{actionError}</p>}

    <div className={styles.tabs} role="tablist" aria-label="Changes by state">
      {TABS.map(([key, label]) => <button key={key} type="button" role="tab" aria-selected={tab === key} className={tab === key ? styles.tabOn : ""} onClick={() => setTab(key)}>
        {label}<em>{data.counts[key] ?? 0}</em>
      </button>)}
    </div>

    {rows.length
      ? <div className={styles.changes}>{rows.map((row) => <Change key={row.id} row={row} busy={busyId === row.id} onAction={onAction} />)}</div>
      : <p className={styles.emptyCard}>{tab === "proposed"
        ? "Nothing proposed. “Check for fixes” looks at the latest scan for fixes FIG can apply: titles, meta descriptions and heading structure, where the connected platform supports them."
        : `No ${tab} changes.`}</p>}

    {blocked.length > 0 && <section className={styles.card} aria-labelledby="blocked-title">
      <div className={styles.cardHead}><div><h2 id="blocked-title">{data.platform ? "Can’t go through the connected site" : "Needs a person"}</h2>
        <p>{data.platform ? "These findings need a person: the connected platform can’t make these edits." : "Connect a site to send the mechanical fixes from here. Everything below needs a person either way."}</p></div></div>
      <ul className={styles.blockedList}>{blocked.map((b) => <li key={b.check}>
        <span className={`${styles.layerTag} ${styles[b.layer] ?? ""}`}>{LAYER_LABEL[b.layer] ?? b.layer}</span>
        <div><strong>{b.title}</strong><span>{b.pages.length ? b.pages.slice(0, 3).join(", ") + (b.pages.length > 3 ? ", …" : "") : "whole site"}</span>{b.fix && <small>Fix: {b.fix}</small>}</div>
      </li>)}</ul>
    </section>}

    {closed.length > 0 && <details className={styles.history}>
      <summary>{closed.length} rejected or reverted</summary>
      <div className={styles.changes}>{closed.map((row) => <Change key={row.id} row={row} busy={busyId === row.id} onAction={onAction} />)}</div>
    </details>}
  </div>;
}
