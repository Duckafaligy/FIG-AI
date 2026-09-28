"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useMemo, useRef, useState } from "react";
import { BarChart3, Check, Copy, Search, X } from "lucide-react";
import { api, type ApiProjectsPage } from "@/lib/api";
import { PlatformMark } from "./dashboard-shell";
import { ProjectActions } from "./project-actions";
import { ProjectConnectors } from "./project-connectors";
import pp from "./project-page.module.css";
import styles from "./projects-list.module.css";

type Card = ApiProjectsPage["cards"][number];
type Filter = "all" | "attention" | "fixing" | "clean";

const WORDS = ["No", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine", "Ten"];
const FILTERS: [Filter, string][] = [["all", "All"], ["attention", "Needs attention"], ["fixing", "Worth fixing"], ["clean", "Clean"]];
const ORDER: Record<Card["status"], number> = { attention: 0, fixing: 1, none: 2, clean: 3 };
const LAYERS = [["craft", "Craft"], ["structure", "Structure"], ["search", "Search"], ["answers", "Answers"]] as const;
const TONE: Record<Card["status"], string> = { attention: "#E0674F", fixing: "#D9A441", clean: "#14C86B", none: "#4A5243" };
const CREATE_WITH = ["wordpress", "shopify", "webflow", "wix", "github"];

const barColour = (v: number) => v >= 80 ? "#14C86B" : v >= 50 ? "#D9A441" : "#E0674F";
const projectUrl = (host: string) => `/projects/${encodeURIComponent(host)}`;

function statusText(card: Card): string {
  const s = card.scan;
  if (!s) return "No scan yet";
  if (card.status === "attention") return `Needs attention · ${s.high} high finding${s.high === 1 ? "" : "s"}`;
  if (card.status === "clean") return "Clean";
  return "Worth fixing";
}

function Ring({ score, colour }: { score: number | null; colour: string }) {
  const r = 23, c = 2 * Math.PI * r, filled = score === null ? 0 : (score / 100) * c;
  return <svg className={styles.ring} width="56" height="56" viewBox="0 0 56 56" role="img" aria-label={score === null ? "No score yet" : `Score ${score} of 100`}>
    <circle cx="28" cy="28" r={r} fill="none" stroke="#1D2119" strokeWidth="5" />
    {score !== null && <circle cx="28" cy="28" r={r} transform="rotate(-90 28 28)" fill="none" stroke={colour} strokeWidth="5" strokeDasharray={`${filled} ${c}`} />}
    <text x="28" y="33" textAnchor="middle">{score ?? "—"}</text>
  </svg>;
}

function CopyLink({ host }: { host: string }) {
  const [copied, setCopied] = useState(false);
  const copy = async () => {
    try { await navigator.clipboard.writeText(`${window.location.origin}${projectUrl(host)}`); setCopied(true); setTimeout(() => setCopied(false), 1500); } catch { /* clipboard blocked: the path is still visible */ }
  };
  return <button type="button" className={styles.address} onClick={copy} aria-label={`Copy the link to ${host}`}>
    <span><i>/projects/</i>{host}</span>{copied ? <Check size={13} /> : <Copy size={13} />}
  </button>;
}

function Row({ card, onChange }: { card: Card; onChange: () => void }) {
  const tone = TONE[card.status];
  const s = card.scan;
  return <article className={styles.row} style={{ borderLeftColor: tone }} data-status={card.status}>
    <div className={styles.identity}>
      <Ring score={card.impact} colour={tone} />
      <div>
        <Link href={projectUrl(card.hostname)} className={styles.name}>{card.name}</Link>
        <span className={styles.host}>{card.hostname}</span>
        <span className={styles.status} style={{ color: card.status === "none" ? undefined : tone }}><i style={{ background: tone }} />{statusText(card)}</span>
      </div>
    </div>
    <div className={styles.layers} aria-label="Score by layer">
      {LAYERS.map(([key, label]) => {
        const v = s?.layers[key] ?? null;
        return <div key={key}><span>{label}</span><i><b style={{ width: `${v ?? 0}%`, background: v === null ? undefined : barColour(v) }} /></i><em>{v ?? "—"}</em></div>;
      })}
    </div>
    <div className={styles.count}>
      <strong>{s ? s.findings : "—"}</strong>
      <span>open finding{s?.findings === 1 ? "" : "s"}</span>
      <small>{s ? `${s.pages} page${s.pages === 1 ? "" : "s"} · scanned ${s.ago}` : "Scan to see findings"}</small>
    </div>
    <div className={styles.connected}>
      <span>Connected</span>
      {card.platforms.length
        ? <div className={styles.marks}>{card.platforms.map((p) => <i key={p} title={p}><PlatformMark platform={p} size={14} /></i>)}</div>
        : <Link href={`${projectUrl(card.hostname)}/settings`} className={styles.connectLink}>Nothing yet · connect</Link>}
    </div>
    <div className={styles.actions}>
      <CopyLink host={card.hostname} />
      <div className={styles.actionRow}><ProjectActions id={card.id} name={card.name} onChange={onChange} />
        <Link href={projectUrl(card.hostname)} className={card.status === "attention" ? pp.primarySmall : styles.openQuiet}>Open project →</Link></div>
    </div>
  </article>;
}

/** Every project in the workspace (Paper 2.2), sorted by what needs a person
 *  first. Each row's status follows fixed rules on the latest scan
 *  (app/pages.py:_card_reading); nothing is estimated. */
export function ProjectsList() {
  const router = useRouter();
  const dialog = useRef<HTMLDialogElement>(null);
  const [data, setData] = useState<ApiProjectsPage | null>(null);
  const [error, setError] = useState("");
  const [query, setQuery] = useState("");
  const [filter, setFilter] = useState<Filter>("all");

  const load = () => {
    api.projects().then((result) => {
      if (result.ok) { setData(result.data); setError(""); }
      else if (result.status === 402) window.location.replace("/choose-plan");
      else setError(result.status === 401 ? "Your session expired. Please sign in again." : "Couldn’t load your projects. Refresh to try again.");
    });
  };
  useEffect(load, []);

  const cards = useMemo(() => [...(data?.cards ?? [])].sort((a, b) =>
    ORDER[a.status] - ORDER[b.status] || (a.impact ?? 101) - (b.impact ?? 101)), [data]);
  const counts = useMemo(() => Object.fromEntries(FILTERS.map(([f]) =>
    [f, f === "all" ? cards.length : cards.filter((c) => c.status === f).length])) as Record<Filter, number>, [cards]);
  const visible = cards.filter((c) => (filter === "all" || c.status === filter)
    && `${c.name} ${c.hostname}`.toLowerCase().includes(query.trim().toLowerCase()));

  if (error) return <p className="form-message" role="alert">{error}</p>;
  if (!data) return <p className={pp.empty} role="status">Loading your projects…</p>;

  const n = cards.length;
  const limit = data.limit;
  const slots = limit ? Math.max(0, limit.max - n) : null;
  const created = (project: { id: string; hostname: string }) => { dialog.current?.close(); router.push(projectUrl(project.hostname)); };

  return <div className={pp.page}>
    <header className={pp.head}>
      <div>
        <span className={pp.eyebrow}>Projects</span>
        <h1>{n === 0 ? "No projects yet." : n === 1 ? "One project, one address." : `${WORDS[n] ?? n} projects, one address each.`}</h1>
        <p>Every project opens at its own link. Bookmark it, or send it to a teammate and it lands straight on that project.</p>
      </div>
      <div className={pp.headActions}>
        {n > 0 && <label className={styles.search}><Search size={14} aria-hidden="true" /><input aria-label="Search projects" placeholder="Search projects" value={query} onChange={(e) => setQuery(e.target.value)} /></label>}
        <button type="button" className={pp.primary} onClick={() => dialog.current?.showModal()} disabled={slots === 0} title={slots === 0 ? `Every ${limit!.plan} slot is in use` : undefined}>+ Add project</button>
      </div>
    </header>

    {data.demo && <div className={pp.banner} role="status"><div><strong>Sample workspace</strong><span>These projects and figures are seeded for exploring the interface.</span></div></div>}

    {n > 0 && <div className={styles.filterBar}>
      <div className={pp.tabs} role="tablist" aria-label="Filter projects">
        {FILTERS.map(([key, label]) => <button key={key} type="button" role="tab" aria-selected={filter === key} className={filter === key ? pp.tabOn : ""} onClick={() => setFilter(key)}>{label}<em>{counts[key]}</em></button>)}
      </div>
      <span className={styles.sortNote}>Sorted by what needs you first</span>
    </div>}

    {n > 0 && (visible.length
      ? <div className={styles.list}>{visible.map((card) => <Row key={card.id} card={card} onChange={load} />)}</div>
      : <p className={pp.emptyCard}>No projects match. <button type="button" className={styles.inlineButton} onClick={() => { setQuery(""); setFilter("all"); }}>Show all</button></p>)}

    <button type="button" className={styles.add} onClick={() => dialog.current?.showModal()} disabled={slots === 0}>
      <div>
        <strong>{n === 0 ? "Add your first project" : "Add a project"}</strong>
        <span>Connect the website’s CMS or repository and FIG creates the project from it.{limit && ` ${slots} of ${limit.max} slot${limit.max === 1 ? "" : "s"} left on ${limit.plan}.`}</span>
      </div>
      <div className={styles.marks} aria-hidden="true">{CREATE_WITH.map((p) => <i key={p}><PlatformMark platform={p} size={14} /></i>)}</div>
    </button>

    <dialog ref={dialog} className={`preview-info-dialog ${styles.dialog}`} aria-labelledby="add-project-title">
      <div><h2 id="add-project-title">Add a project</h2><button type="button" aria-label="Close" onClick={() => dialog.current?.close()}><X size={18} /></button></div>
      <div className={styles.dialogBody}>
        <p>Connect the platform this site runs on. FIG creates the project and queues its first scan.</p>
        <ProjectConnectors apis={[]} compact onCreated={created} />
        <p className="project-connectors-compact-note"><BarChart3 size={13} />Google Analytics and Search Console connect from <Link href="/projects/settings">account settings</Link>.</p>
      </div>
    </dialog>
  </div>;
}
