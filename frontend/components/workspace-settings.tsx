"use client";

import Link from "next/link";
import { useEffect, useState, type FormEvent } from "react";
import { actions, api, apiUrl, type ApiConnectionItem, type ApiWorkspaceSettings } from "@/lib/api";
import { PlatformMark } from "./dashboard-shell";
import pp from "./project-page.module.css";
import styles from "./workspace-settings.module.css";

type Tab = "workspace" | "connections" | "team" | "billing";
const TABS: [Tab, string][] = [["workspace", "Workspace"], ["connections", "Connections"], ["team", "Team"], ["billing", "Billing"]];
const WORDS = ["No", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine", "Ten"];
const PLATFORM_NAMES: Record<string, string> = { wordpress: "WordPress", shopify: "Shopify", webflow: "Webflow", wix: "Wix", github: "GitHub" };
const count = (n: number, noun: string) => `${WORDS[n] ?? n} ${noun}${n === 1 ? "" : "s"}`;
const dollars = (cents: number) => `$${(cents / 100).toFixed(cents % 100 ? 2 : 0)}`;
const scoreTone = (s: number | null) => s === null ? "#4a5243" : s >= 80 ? "#14c86b" : s >= 50 ? "#d9a441" : "#e0674f";
const projectHref = (host: string, suffix = "") => `/projects/${encodeURIComponent(host)}${suffix}`;

function Meter({ used, max }: { used: number; max: number | null }) {
  return <i className={styles.meter}><b style={{ width: max ? `${Math.min(100, (used / Math.max(1, max)) * 100)}%` : "0%" }} /></i>;
}

function WorkspaceTab({ data, reload }: { data: ApiWorkspaceSettings; reload: () => void }) {
  const [name, setName] = useState(data.profile.name);
  const [msg, setMsg] = useState("");
  const [busy, setBusy] = useState<string | null>(null);
  const [confirm, setConfirm] = useState("");
  const [deleteOpen, setDeleteOpen] = useState(false);
  const [deleted, setDeleted] = useState(false);

  const rename = async (e: FormEvent) => {
    e.preventDefault(); setBusy("rename"); setMsg("");
    const r = await actions.renameWorkspace(name.trim());
    setBusy(null);
    if (!r.ok) { setMsg(r.error); return; }
    setMsg("Saved."); reload();
  };
  const share = async (id: string, on: boolean) => {
    setBusy(id); setMsg("");
    const r = await actions.shareProject(id, on);
    setBusy(null);
    if (!r.ok) { setMsg(r.error); return; }
    reload();
  };
  const remove = async (e: FormEvent) => {
    e.preventDefault(); setBusy("delete"); setMsg("");
    const r = await actions.deleteAccount(confirm);
    setBusy(null);
    if (!r.ok) { setMsg(r.error); return; }
    setDeleted(true);
  };

  if (deleted) return <section className={pp.card} role="status"><div className={pp.cardHead}><div><h2>Workspace deleted</h2><p>Every project, scan, draft and stored credential is gone. Stripe keeps your invoices.</p></div></div><a className={pp.primarySmall} href="/">Back to the homepage</a></section>;

  return <>
    {msg && <p className="form-message" role="status">{msg}</p>}
    <section className={pp.card} aria-labelledby="ws-title">
      <div className={pp.cardHead}><div><h2 id="ws-title">Workspace</h2><p>The name on reports and invoices.</p></div></div>
      <form className={styles.fields} onSubmit={rename}>
        <label><span>Name</span><div className={styles.inline}><input value={name} maxLength={80} onChange={(e) => setName(e.target.value)} />
          <button type="submit" className={pp.ghost} disabled={busy !== null || name.trim() === data.profile.name || name.trim().length < 2}>{busy === "rename" ? "Saving…" : "Save"}</button></div></label>
        <label><span>Billing email</span><input value={data.profile.email || "Not set"} readOnly aria-readonly="true" /><small>Invoices and receipts go here. Change it in the Stripe portal.</small></label>
      </form>
    </section>

    <section className={pp.card} aria-labelledby="ws-projects">
      <div className={pp.cardHead}><div><h2 id="ws-projects">Projects</h2><p>Scheduled scans need ownership verified. One-off scans of any site never do.</p></div>
        <Link className={pp.primarySmall} href="/projects">Add project</Link></div>
      {data.projects.length ? <div className={styles.tableWrap}><table className={pp.table}>
        <thead><tr><th>Project</th><th>Site</th><th>Publishes via</th><th>Ownership</th><th>Scans</th><th>Public report</th><th><span className={styles.sr}>Edit</span></th></tr></thead>
        <tbody>{data.projects.map((p) => <tr key={p.id}>
          <td><span className={styles.projectTag}><i style={{ background: scoreTone(p.score) }} />{p.name}</span></td>
          <td className={pp.pathCell}>{p.hostname}</td>
          <td>{p.platform ? <span className={styles.chip}><PlatformMark platform={p.platform} size={12} />{PLATFORM_NAMES[p.platform] ?? p.platform}</span> : <span className={styles.muted}>Nothing yet</span>}</td>
          <td>{p.verified ? <span className={styles.ok}>Verified</span> : <span className={styles.muted}>Not verified</span>}</td>
          <td>{p.scans}</td>
          <td><button type="button" role="switch" aria-checked={p.public} aria-label={`Public report for ${p.name}`} className={styles.switch} disabled={busy !== null || (!p.can_share && !p.public)} title={!p.can_share ? "Run a scan first" : undefined} onClick={() => share(p.id, !p.public)}><i /></button></td>
          <td><Link className={styles.edit} href={projectHref(p.hostname, "/settings")}>Edit</Link></td>
        </tr>)}</tbody>
      </table></div> : <p className={pp.empty}>No projects yet.</p>}
    </section>

    <section className={`${pp.card} ${styles.danger}`} aria-labelledby="ws-delete">
      <div className={pp.cardHead}><div><h2 id="ws-delete">Delete this workspace</h2><p>Cancels the subscription first, then deletes every project, scan, draft and stored credential. Stripe keeps your invoices.</p></div>
        {!deleteOpen && <button type="button" className={styles.dangerButton} onClick={() => setDeleteOpen(true)}>Delete workspace</button>}</div>
      {deleteOpen && <form className={styles.deleteForm} onSubmit={remove}>
        <label><span>Type your account email to confirm</span><input value={confirm} onChange={(e) => setConfirm(e.target.value)} autoComplete="off" /></label>
        <div className={styles.inline}><button type="submit" className={styles.dangerButton} disabled={busy !== null || !confirm.includes("@")}>{busy === "delete" ? "Deleting…" : "Delete everything"}</button>
          <button type="button" className={pp.ghost} onClick={() => { setDeleteOpen(false); setConfirm(""); }}>Cancel</button></div>
      </form>}
    </section>
  </>;
}

function ConnectionRow({ c, host }: { c: ApiConnectionItem; host?: string }) {
  return <li className={c.ok ? styles.conn : styles.connBad}>
    <span className={styles.mark}><PlatformMark platform={c.platform} size={15} /></span>
    <div><strong>{c.label} <em>{c.kind === "cms" ? "CMS · write" : "data · read"}</em></strong>
      <span>{c.ok ? [c.detail, c.since && `since ${c.since}`].filter(Boolean).join(" · ") || "Connected" : c.error}</span></div>
    <b className={c.ok ? styles.ok : styles.bad}>{c.ok ? "Connected" : "Needs attention"}</b>
    {host && <Link className={c.ok ? pp.ghost : pp.primarySmall} href={projectHref(host, "/settings")}>{c.ok ? "Manage" : "Reconnect"}</Link>}
  </li>;
}

function ConnectionsTab({ data }: { data: ApiWorkspaceSettings }) {
  return <>
    <div className={styles.legend}><span><i className={styles.lgOk} />Connected</span><span><i className={styles.lgBad} />Needs attention</span><span><i className={styles.lgOpen} />Open slot</span></div>
    <section className={pp.card} aria-labelledby="conn-ws">
      <div className={pp.cardHead}><div><h2 id="conn-ws">Workspace-wide</h2><p>One Google sign-in covers Search Console and Analytics for every project.</p></div>
        <a className={data.workspace_connections.some((c) => !c.ok) || !data.workspace_connections.length ? pp.primarySmall : pp.ghost} href={apiUrl("/oauth/google/start")}>{data.workspace_connections.length ? "Reconnect Google" : "Connect Google"}</a></div>
      {data.workspace_connections.length
        ? <ul className={`${styles.connList} ${styles.wsList}`}>{data.workspace_connections.map((c) => <ConnectionRow key={c.platform} c={c} />)}</ul>
        : <p className={pp.empty}>Not connected. Search Console and Analytics numbers stay blank until it is.</p>}
    </section>
    {data.connections.map((p) => {
      const hasCms = p.items.some((i) => i.kind === "cms");
      const hasGoogle = p.items.some((i) => i.kind === "data") || data.workspace_connections.length > 0;
      return <section className={styles.projectConn} key={p.hostname} aria-label={p.project}>
        <div className={styles.projectCard} style={{ borderTopColor: scoreTone(p.score) }}>
          <strong>{p.project}</strong><span className={styles.mono}>{p.hostname}</span>
          <small>{p.score !== null ? `Score ${p.score} · ` : ""}{count(p.items.length, "connection").toLowerCase()}</small>
        </div>
        <ul className={styles.connList}>
          {p.items.map((c) => <ConnectionRow key={c.platform} c={c} host={p.hostname} />)}
          {!hasCms && <li className={styles.slot}><Link href={projectHref(p.hostname, "/settings")}>+ Connect a CMS or repository</Link></li>}
          {!hasGoogle && <li className={styles.slot}><a href={apiUrl("/oauth/google/start")}>+ Connect Search Console or Analytics</a></li>}
        </ul>
      </section>;
    })}
    <section className={`${pp.card} ${styles.rules}`}>
      <div><span className={pp.sectionLabel}>CMS · one per project</span><div className={styles.chips}>{["wordpress", "shopify", "webflow", "wix", "github"].map((p) => <span key={p} className={styles.chip}><PlatformMark platform={p} size={12} />{PLATFORM_NAMES[p]}</span>)}</div></div>
      <div><span className={pp.sectionLabel}>Data · any number</span><div className={styles.chips}>{["google_search_console", "google_analytics"].map((p) => <span key={p} className={styles.chip}><PlatformMark platform={p} size={12} />{p === "google_analytics" ? "Analytics" : "Search Console"}</span>)}</div></div>
      <p>Tokens are encrypted and deleted when you disconnect.</p>
    </section>
  </>;
}

function TeamTab({ data }: { data: ApiWorkspaceSettings }) {
  return <section className={pp.card} aria-labelledby="team-title">
    <div className={pp.cardHead}><div><h2 id="team-title">Who’s in this workspace</h2>
      <p>Everyone here can open every project. Per-project roles and invites aren’t built yet, so nobody is added from this page.</p></div></div>
    {data.team.length ? <ul className={styles.people}>{data.team.map((u) => <li key={u.email}>
      <span className={styles.avatar}>{u.initials}</span>
      <div><strong>{u.email}</strong><span>{u.role}</span></div>
      <small>Joined {u.since}</small>
    </li>)}</ul> : <p className={pp.empty}>No sign-ins recorded for this workspace.</p>}
  </section>;
}

function BillingTab({ data }: { data: ApiWorkspaceSettings }) {
  const b = data.billing;
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState("");
  const go = async (plan?: string) => {
    setBusy(plan ?? "portal"); setError("");
    const r = plan ? await actions.startCheckout(plan) : await actions.startPortal();
    if (!r.ok) { setError(r.error); setBusy(null); return; }
    window.location.href = r.data.url;
  };
  return <>
    {error && <p className="form-message" role="alert">{error}</p>}
    <div className={styles.usage}>
      <div><div className={styles.usageTop}><span>Projects</span><b>{b.projects.used}{b.projects.max !== null && ` / ${b.projects.max}`}</b></div><Meter used={b.projects.used} max={b.projects.max} />
        <p>{b.projects.max === null ? "No plan limit on this workspace." : b.projects.max - b.projects.used > 0 ? `${count(b.projects.max - b.projects.used, "more project")} fit on this plan.` : "Every slot on this plan is in use."}</p></div>
      <div><div className={styles.usageTop}><span>Scans this period</span><b>{b.scans ? `${b.scans.used} / ${b.scans.cap}` : "—"}</b></div><Meter used={b.scans?.used ?? 0} max={b.scans?.cap ?? null} />
        <p>{b.scans ? "Resets with your billing period." : "No scan allowance applies without a plan."}</p></div>
      <div><div className={styles.usageTop}><span>Invoices and card</span></div>
        <p>{b.subscribed ? "Receipts, the card on file and cancellation live in Stripe." : b.plan ? "No Stripe subscription on this workspace, so there are no invoices." : "Nothing to manage until you choose a plan."}</p>
        {b.subscribed && <button type="button" className={pp.ghost} disabled={busy !== null} onClick={() => go()}>{busy === "portal" ? "Opening…" : "Manage in Stripe"}</button>}</div>
    </div>
    <div className={styles.plansHead}><h2>Compare plans</h2><p>Every plan runs the same checks. Plans differ in projects and scans.</p></div>
    <div className={styles.plans}>{b.plans.map((p) => {
      const current = p.id === b.plan;
      const tooMany = b.projects.used > p.max_projects;
      return <article key={p.id} className={current ? styles.planOn : styles.plan}>
        <div className={styles.planTop}><strong>{p.label}</strong>{current && <em>Current plan</em>}</div>
        <div className={styles.price}>{dollars(p.price_cents)}<span>/ month</span></div>
        <ul><li>{count(p.max_projects, "project")}</li><li>{p.scans_per_period} scans a month</li></ul>
        {current ? <span className={styles.planState}>You’re on this plan</span>
          : tooMany ? <span className={styles.planBlocked}>Needs {p.max_projects} project{p.max_projects === 1 ? "" : "s"} or fewer</span>
            : b.subscribed ? <button type="button" className={pp.ghost} disabled={busy !== null} onClick={() => go()}>Switch in Stripe</button>
              : <button type="button" className={pp.primarySmall} disabled={busy !== null} onClick={() => go(p.id)}>{busy === p.id ? "Opening…" : `Choose ${p.label}`}</button>}
      </article>;
    })}</div>
    <p className={styles.footnote}>Receipts come from Stripe. The 14-day refund window covers your first payment.</p>
  </>;
}

/** Workspace settings (Paper 3.1-3.4). Everything shown is read from the
 *  workspace (app/pages.py:workspace_settings); what isn't built says so. */
export function WorkspaceSettings() {
  const [data, setData] = useState<ApiWorkspaceSettings | null>(null);
  const [error, setError] = useState("");
  const [tab, setTab] = useState<Tab>("workspace");
  const [notice, setNotice] = useState("");

  const load = () => api.workspaceSettings().then((r) => {
    if (r.ok) { setData(r.data); setError(""); }
    else if (r.status === 402) window.location.replace("/choose-plan");
    else setError(r.status === 401 ? "Your session expired. Please sign in again." : "Couldn’t load workspace settings. Refresh to try again.");
  });
  useEffect(() => {
    const q = new URLSearchParams(window.location.search);
    const t = q.get("tab");
    if (TABS.some(([k]) => k === t)) setTab(t as Tab);
    // Back from Google's consent screen (app/oauth.py sends integration=… and connected=1, or error=…).
    if (q.get("connected") === "1" || q.get("error")) {
      setTab("connections");
      setNotice(q.get("error") ? `Google didn’t connect: ${q.get("error")}` : "Google connected. Search Console and Analytics now read from it.");
      window.history.replaceState(null, "", "?tab=connections");
    }
    load();
  }, []);
  const pick = (t: Tab) => { setTab(t); window.history.replaceState(null, "", t === "workspace" ? "?" : `?tab=${t}`); };

  if (error) return <p className="form-message" role="alert">{error}</p>;
  if (!data) return <p className={pp.empty} role="status">Loading workspace settings…</p>;

  const b = data.billing;
  const bad = data.connections.flatMap((p) => p.items.filter((i) => !i.ok).map((i) => `${p.project}’s ${i.label}`))
    .concat(data.workspace_connections.filter((i) => !i.ok).map((i) => i.label));
  const heads: Record<Tab, [string, string]> = {
    workspace: [data.profile.name, `${count(data.projects.length, "project")}, one bill. Settings here apply across every project.`],
    connections: ["What each project is plugged into.", bad.length ? `Every connection belongs to one project. Needs you: ${bad.join(", ")}.` : "Every connection belongs to one project. Nothing needs reconnecting."],
    team: [data.team.length === 1 ? "Just you, for now." : `${count(data.team.length, "person").replace("persons", "people")} in this workspace.`, "Results are never shared outside the workspace unless a project’s public report link is on."],
    billing: [b.label && b.price_cents !== null ? `${b.label}, ${dollars(b.price_cents)} a month.` : b.subscribed ? "Legacy per-site billing." : "No plan yet.", b.subscribed ? "Cancel any time and it runs to the end of the period." : b.plan ? "Included on this workspace without a Stripe subscription." : "Choose a plan to scan and publish from the workspace."],
  };

  return <div className={pp.page}>
    <header className={pp.head}><div>
      <span className={pp.eyebrow}>Workspace settings</span>
      <h1>{heads[tab][0]}</h1>
      <p>{heads[tab][1]}</p>
    </div></header>
    {notice && <p className="form-message" role="status">{notice}</p>}
    <div className={styles.tabs} role="tablist" aria-label="Workspace settings">
      {TABS.map(([key, label]) => <button key={key} type="button" role="tab" aria-selected={tab === key} className={tab === key ? styles.tabOn : ""} onClick={() => pick(key)}>{label}</button>)}
    </div>
    {tab === "workspace" && <WorkspaceTab data={data} reload={load} />}
    {tab === "connections" && <ConnectionsTab data={data} />}
    {tab === "team" && <TeamTab data={data} />}
    {tab === "billing" && <BillingTab data={data} />}
  </div>;
}
